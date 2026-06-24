#include "main.h"
#include "pros/apix.h"
#include "pros/misc.hpp"
#include "pros/rtos.hpp"
#include "pros/screen.hpp"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <string>

// Safe first-pass V5 Brain bridge for the Pi/ROS serial stack.
//
// This firmware proves bidirectional USB JSON without moving the robot:
// heartbeat/stop packets ack `ok`, motion-bearing packets ack `rejected`, and
// Brain battery/watchdog telemetry streams separately for the ROS demux.

namespace {
constexpr int WATCHDOG_MS = 250;
constexpr int TELEMETRY_MS = 500;
constexpr int MAX_LINE_BYTES = 512;

volatile uint32_t last_packet_ms = 0;
volatile bool estop_latched = false;
volatile bool watchdog_fault = false;

pros::Mutex stdout_mutex;

void emit_json(const char* fmt, ...) {
	if (stdout_mutex.take(100)) {
		va_list args;
		va_start(args, fmt);
		std::vprintf(fmt, args);
		va_end(args);
		std::printf("\n");
		std::fflush(stdout);
		stdout_mutex.give();
	}
}

bool contains(const std::string& line, const char* needle) {
	return line.find(needle) != std::string::npos;
}

int extract_int_field(const std::string& line, const char* field, int fallback = -1) {
	const std::string key = std::string("\"") + field + "\"";
	const auto key_pos = line.find(key);
	if (key_pos == std::string::npos) return fallback;

	const auto colon_pos = line.find(':', key_pos + key.size());
	if (colon_pos == std::string::npos) return fallback;

	const char* raw = line.c_str() + colon_pos + 1;
	while (*raw == ' ' || *raw == '\t') raw++;
	return std::atoi(raw);
}

bool has_json_value(const std::string& line, const char* key, const char* value) {
	return contains(line, key) && contains(line, value);
}

uint32_t packet_age_ms() {
	const uint32_t now = pros::millis();
	const uint32_t last = last_packet_ms;
	return now >= last ? now - last : 0;
}

void stop_drive(const char* reason) {
	(void)reason;
	// No motors are mapped in this proof firmware. Keep this hook as the single
	// place that future drivetrain/arm ports must be stopped.
}

void emit_ack(int seq, const char* state, const char* fault_json = "null") {
	emit_json(
	    "{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\",\"recv_ms\":%lu,"
	    "\"battery_mv\":%ld,\"battery_pct\":%.1f,\"watchdog_age_ms\":%lu,"
	    "\"estop\":%s,\"fault\":%s}",
	    seq,
	    state,
	    static_cast<unsigned long>(pros::millis()),
	    static_cast<long>(pros::battery::get_voltage()),
	    pros::battery::get_capacity(),
	    static_cast<unsigned long>(packet_age_ms()),
	    estop_latched ? "true" : "false",
	    fault_json);
}

void emit_status(const char* state, const char* reason, const char* message) {
	emit_json(
	    "{\"v\":1,\"type\":\"bridge_status\",\"state\":\"%s\",\"reason\":\"%s\","
	    "\"message\":\"%s\",\"observed_ms\":%lu}",
	    state,
	    reason,
	    message,
	    static_cast<unsigned long>(pros::millis()));
}

void emit_telemetry() {
	emit_json(
	    "{\"v\":1,\"type\":\"telemetry\",\"t_ms\":%lu,\"battery_mv\":%ld,"
	    "\"battery_current_ma\":%ld,\"battery_pct\":%.1f,\"battery_temp_c\":%.1f,"
	    "\"watchdog_age_ms\":%lu,\"estop\":%s,\"motion_enabled\":false}",
	    static_cast<unsigned long>(pros::millis()),
	    static_cast<long>(pros::battery::get_voltage()),
	    static_cast<long>(pros::battery::get_current()),
	    pros::battery::get_capacity(),
	    pros::battery::get_temperature(),
	    static_cast<unsigned long>(packet_age_ms()),
	    estop_latched ? "true" : "false");
}

void handle_line(const std::string& line) {
	const int seq = extract_int_field(line, "seq");
	if (seq < 0) {
		emit_status("warn", "bad_packet", "Brain received a packet without an integer seq");
		return;
	}

	last_packet_ms = pros::millis();
	watchdog_fault = false;

	if (has_json_value(line, "\"type\"", "\"heartbeat\"")) {
		emit_ack(seq, "ok");
		return;
	}

	if (!has_json_value(line, "\"type\"", "\"cmd\"")) {
		stop_drive("unknown packet type");
		emit_ack(seq, "rejected", "\"unknown_packet_type\"");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"stop\"")) {
		estop_latched = contains(line, "operator_estop");
		stop_drive("stop command");
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"drive\"") ||
	    has_json_value(line, "\"cmd\"", "\"turn\"") ||
	    has_json_value(line, "\"cmd\"", "\"set_goal\"")) {
		stop_drive("motion command rejected");
		emit_ack(seq, "rejected", "\"motion_disabled\"");
		return;
	}

	stop_drive("unknown command");
	emit_ack(seq, "rejected", "\"unknown_command\"");
}

void receive_task(void*) {
	std::string line;
	line.reserve(MAX_LINE_BYTES);

	while (true) {
		const int ch = std::getchar();
		if (ch == EOF) {
			pros::delay(2);
			continue;
		}

		if (ch == '\r') {
			continue;
		}
		if (ch == '\n') {
			if (!line.empty()) {
				handle_line(line);
				line.clear();
			}
			continue;
		}

		if (line.size() < MAX_LINE_BYTES) {
			line.push_back(static_cast<char>(ch));
		} else {
			line.clear();
			stop_drive("oversized packet");
			emit_status("warn", "oversized_packet", "discarded serial packet above 512 bytes");
		}
	}
}

void watchdog_task(void*) {
	while (true) {
		if (packet_age_ms() > WATCHDOG_MS) {
			stop_drive("watchdog");
			if (!watchdog_fault) {
				watchdog_fault = true;
				emit_status("fault", "watchdog_stop", "no valid packet before watchdog timeout");
			}
		}
		pros::delay(20);
	}
}

void telemetry_task(void*) {
	while (true) {
		emit_telemetry();
		pros::delay(TELEMETRY_MS);
	}
}
}  // namespace

void initialize() {
	pros::c::serctl(SERCTL_DISABLE_COBS, nullptr);
	last_packet_ms = pros::millis();

	pros::screen::set_pen(pros::c::COLOR_WHITE);
	pros::screen::print(pros::E_TEXT_LARGE, 1, "vexy serial bridge");
	pros::screen::print(pros::E_TEXT_MEDIUM, 3, "motion disabled");

	emit_status("ok", "brain_bridge_ready", "safe ack/telemetry bridge initialized");
}

void opcontrol() {
	pros::Task rx_task(receive_task, nullptr, "vex_rx");
	pros::Task watchdog(watchdog_task, nullptr, "vex_watchdog");
	pros::Task telemetry(telemetry_task, nullptr, "vex_telem");

	while (true) {
		pros::delay(1000);
	}
}

void disabled() {}
void autonomous() {}
void competition_initialize() {}
