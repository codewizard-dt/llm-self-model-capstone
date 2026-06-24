#include "main.h"
#include "pros/apix.h"
#include "pros/misc.hpp"
#include "pros/motors.hpp"
#include "pros/rtos.hpp"
#include "pros/screen.hpp"

#include <cstdarg>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

// Guarded V5 Brain bridge for the Pi/ROS serial stack.
//
// It keeps command acknowledgements and telemetry as separate JSON records,
// stops on watchdog/TTL expiry, and only enables drivetrain motion when the
// expected two-drive Clawbot motor ports are present.

namespace {
constexpr int WATCHDOG_MS = 250;
constexpr int TELEMETRY_MS = 500;
constexpr int MAX_LINE_BYTES = 2048;
constexpr int LEFT_DRIVE_PORT = 1;
constexpr int RIGHT_DRIVE_PORT = 10;
constexpr int MAX_TTL_MS = 500;
constexpr int MAX_DRIVE_RPM = 45;
constexpr int MAX_TURN_RPM = 35;
constexpr int DRIVE_CURRENT_LIMIT_MA = 1500;
constexpr int DRIVE_VOLTAGE_LIMIT_MV = 6000;
constexpr double WHEEL_CIRCUMFERENCE_M = 0.319;  // 4 in wheel.
constexpr double TRACK_WIDTH_M = 0.28;
constexpr double DRIVE_FORWARD_SIGN = -1.0;

volatile uint32_t last_packet_ms = 0;
volatile uint32_t motion_until_ms = 0;
volatile bool estop_latched = false;
volatile bool watchdog_fault = false;

pros::Mutex stdout_mutex;

pros::Motor& left_drive() {
	static pros::Motor motor(LEFT_DRIVE_PORT);
	return motor;
}

pros::Motor& right_drive() {
	static pros::Motor motor(-RIGHT_DRIVE_PORT);
	return motor;
}

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

double extract_double_field(const std::string& line, const char* field, double fallback = 0.0) {
	const std::string key = std::string("\"") + field + "\"";
	const auto key_pos = line.find(key);
	if (key_pos == std::string::npos) return fallback;

	const auto colon_pos = line.find(':', key_pos + key.size());
	if (colon_pos == std::string::npos) return fallback;

	const char* raw = line.c_str() + colon_pos + 1;
	while (*raw == ' ' || *raw == '\t') raw++;
	return std::atof(raw);
}

bool has_json_value(const std::string& line, const char* key, const char* value) {
	return contains(line, key) && contains(line, value);
}

double clamp(double value, double lo, double hi) {
	if (value < lo) return lo;
	if (value > hi) return hi;
	return value;
}

uint32_t packet_age_ms() {
	const uint32_t now = pros::millis();
	const uint32_t last = last_packet_ms;
	return now >= last ? now - last : 0;
}

uint32_t motion_age_ms() {
	const uint32_t until = motion_until_ms;
	if (until == 0) return 0;
	const uint32_t now = pros::millis();
	return now >= until ? now - until : 0;
}

std::vector<int> connected_motor_ports() {
	std::vector<int> ports;
	for (const pros::Motor& motor : pros::Motor::get_all_devices()) {
		int port = static_cast<int>(motor.get_port());
		if (port < 0) port = -port;
		ports.push_back(port);
	}
	return ports;
}

bool motor_port_present(int port) {
	for (int connected : connected_motor_ports()) {
		if (connected == port) return true;
	}
	return false;
}

bool drive_ports_ok() {
	return motor_port_present(LEFT_DRIVE_PORT) && motor_port_present(RIGHT_DRIVE_PORT);
}

bool motion_enabled() {
	return drive_ports_ok() && !estop_latched;
}

std::string motor_ports_json() {
	std::string out = "[";
	bool first = true;
	for (int port : connected_motor_ports()) {
		if (!first) out += ",";
		char buf[8];
		std::snprintf(buf, sizeof(buf), "%d", port);
		out += buf;
		first = false;
	}
	out += "]";
	return out;
}

void configure_drive() {
	if (!drive_ports_ok()) return;
	left_drive().set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
	right_drive().set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
	left_drive().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
	right_drive().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
	left_drive().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
	right_drive().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
	left_drive().tare_position();
	right_drive().tare_position();
}

void stop_drive(const char* reason) {
	(void)reason;
	motion_until_ms = 0;
	if (!drive_ports_ok()) return;
	left_drive().move_velocity(0);
	right_drive().move_velocity(0);
	left_drive().brake();
	right_drive().brake();
}

void set_drive(double vx_mps, double omega_rad_s, int ttl_ms) {
	const double rpm_per_mps = 60.0 / WHEEL_CIRCUMFERENCE_M;
	const double signed_vx_mps = DRIVE_FORWARD_SIGN * vx_mps;
	const double turn_mps = omega_rad_s * (TRACK_WIDTH_M / 2.0);
	const double rpm_limit = std::abs(signed_vx_mps) < 0.001 ? MAX_TURN_RPM : MAX_DRIVE_RPM;
	const int left_rpm = static_cast<int>(clamp((signed_vx_mps - turn_mps) * rpm_per_mps,
	                                           -rpm_limit, rpm_limit));
	const int right_rpm = static_cast<int>(clamp((signed_vx_mps + turn_mps) * rpm_per_mps,
	                                            -rpm_limit, rpm_limit));

	left_drive().move_velocity(left_rpm);
	right_drive().move_velocity(right_rpm);
	motion_until_ms = pros::millis() + static_cast<uint32_t>(ttl_ms);
}

std::string motor_sample_json(const char* device, pros::Motor& motor, uint32_t sample_ms) {
	char buf[768];
	std::snprintf(
	    buf,
	    sizeof(buf),
	    "{\"device\":\"%s\",\"subsystem\":\"drivetrain\",\"sample_ms\":%lu,"
	    "\"values\":{\"position_deg\":%.1f,\"velocity_rpm\":%.1f,"
	    "\"current_amp\":%.3f,\"power_w\":%.3f,\"torque_nm\":%.3f,"
	    "\"efficiency_pct\":%.1f,\"temperature_c\":%.1f}}",
	    device,
	    static_cast<unsigned long>(sample_ms),
	    motor.get_position(),
	    motor.get_actual_velocity(),
	    motor.get_current_draw() / 1000.0,
	    motor.get_power(),
	    motor.get_torque(),
	    motor.get_efficiency(),
	    motor.get_temperature());
	return std::string(buf);
}

std::string motor_samples_json(uint32_t sample_ms) {
	if (!drive_ports_ok()) return "[]";
	return std::string("[") + motor_sample_json("left_drive", left_drive(), sample_ms) + "," +
	       motor_sample_json("right_drive", right_drive(), sample_ms) + "]";
}

void emit_ack(int seq, const char* state, const char* fault_json = "null") {
	emit_json(
	    "{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\",\"recv_ms\":%lu,"
	    "\"battery_mv\":%ld,\"battery_pct\":%.1f,\"watchdog_age_ms\":%lu,"
	    "\"estop\":%s,\"motion_enabled\":%s,\"drive_ports_ok\":%s,\"motor_ports\":%s,"
	    "\"fault\":%s}",
	    seq,
	    state,
	    static_cast<unsigned long>(pros::millis()),
	    static_cast<long>(pros::battery::get_voltage()),
	    pros::battery::get_capacity(),
	    static_cast<unsigned long>(packet_age_ms()),
	    estop_latched ? "true" : "false",
	    motion_enabled() ? "true" : "false",
	    drive_ports_ok() ? "true" : "false",
	    motor_ports_json().c_str(),
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
	const uint32_t sample_ms = pros::millis();
	emit_json(
	    "{\"v\":1,\"type\":\"telemetry\",\"t_ms\":%lu,\"battery_mv\":%ld,"
	    "\"battery_current_ma\":%ld,\"battery_pct\":%.1f,\"battery_temp_c\":%.1f,"
	    "\"watchdog_age_ms\":%lu,\"motion_ttl_overrun_ms\":%lu,\"estop\":%s,"
	    "\"motion_enabled\":%s,\"drive_ports_ok\":%s,\"motor_ports\":%s,"
	    "\"left_pos_deg\":%.1f,\"right_pos_deg\":%.1f,"
	    "\"left_vel_rpm\":%.1f,\"right_vel_rpm\":%.1f,\"motor_samples\":%s}",
	    static_cast<unsigned long>(sample_ms),
	    static_cast<long>(pros::battery::get_voltage()),
	    static_cast<long>(pros::battery::get_current()),
	    pros::battery::get_capacity(),
	    pros::battery::get_temperature(),
	    static_cast<unsigned long>(packet_age_ms()),
	    static_cast<unsigned long>(motion_age_ms()),
	    estop_latched ? "true" : "false",
	    motion_enabled() ? "true" : "false",
	    drive_ports_ok() ? "true" : "false",
	    motor_ports_json().c_str(),
	    drive_ports_ok() ? left_drive().get_position() : 0.0,
	    drive_ports_ok() ? right_drive().get_position() : 0.0,
	    drive_ports_ok() ? left_drive().get_actual_velocity() : 0.0,
	    drive_ports_ok() ? right_drive().get_actual_velocity() : 0.0,
	    motor_samples_json(sample_ms).c_str());
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
	    has_json_value(line, "\"cmd\"", "\"turn\"")) {
		if (estop_latched) {
			stop_drive("estop latched");
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (!drive_ports_ok()) {
			stop_drive("drive ports missing");
			emit_ack(seq, "rejected", "\"drive_ports_missing\"");
			return;
		}

		int ttl_ms = extract_int_field(line, "ttl_ms", WATCHDOG_MS);
		if (ttl_ms < 20) ttl_ms = 20;
		if (ttl_ms > MAX_TTL_MS) ttl_ms = MAX_TTL_MS;

		const double vx = has_json_value(line, "\"cmd\"", "\"turn\"")
		                      ? 0.0
		                      : clamp(extract_double_field(line, "vx"), -0.18, 0.18);
		const double omega = clamp(extract_double_field(line, "omega"), -0.6, 0.6);
		set_drive(vx, omega, ttl_ms);
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"set_goal\"")) {
		stop_drive("set_goal not handled by Brain");
		emit_ack(seq, "rejected", "\"unsupported_goal\"");
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
		if (motion_until_ms != 0 && pros::millis() > motion_until_ms) {
			stop_drive("ttl_expired");
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
	configure_drive();

	pros::screen::set_pen(pros::c::COLOR_WHITE);
	pros::screen::print(pros::E_TEXT_LARGE, 1, "vexy serial bridge");
	pros::screen::print(pros::E_TEXT_MEDIUM, 3, "guarded drive ports %d/%d",
	                    LEFT_DRIVE_PORT, RIGHT_DRIVE_PORT);

	emit_status("ok", "brain_bridge_ready", "guarded ack/telemetry bridge initialized");
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
