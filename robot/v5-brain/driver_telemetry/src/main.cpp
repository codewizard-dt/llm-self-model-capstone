#include "main.h"
#include "pros/apix.h"
#include "pros/misc.hpp"
#include "pros/motors.hpp"
#include "pros/rtos.hpp"
#include "pros/screen.hpp"

#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace {
constexpr int TELEMETRY_MS = 200;
constexpr int CONTROL_MS = 20;
constexpr int MAX_LINE_BYTES = 2048;
constexpr int LEFT_DRIVE_PORT = 1;
constexpr int RIGHT_DRIVE_PORT = 10;
constexpr int ARM_PORT = 8;
constexpr int CLAW_PORT = 3;
constexpr int DRIVE_CURRENT_LIMIT_MA = 1500;
constexpr int DRIVE_VOLTAGE_LIMIT_MV = 6000;
constexpr int ARM_CURRENT_LIMIT_MA = 1800;
constexpr int ARM_VOLTAGE_LIMIT_MV = 6000;
constexpr int JOYSTICK_DEADBAND = 5;
constexpr int DRIVE_POWER_LIMIT = 90;
constexpr int ARM_RPM = 65;
constexpr int CLAW_RPM = 100;

volatile uint32_t last_packet_ms = 0;
volatile bool estop_latched = false;
volatile int last_left_cmd = 0;
volatile int last_right_cmd = 0;
volatile int last_arm_cmd = 0;
volatile int last_claw_cmd = 0;
bool drive_ready = false;
bool arm_ready = false;
bool claw_ready = false;

pros::Mutex stdout_mutex;
pros::Mutex controller_mutex;

struct ControllerSnapshot {
	int left_y = 0;
	int right_x = 0;
	bool l1 = false;
	bool l2 = false;
	bool r1 = false;
	bool r2 = false;
	bool a = false;
	bool b = false;
	bool x = false;
	bool y = false;
};

ControllerSnapshot controller_snapshot;

pros::Motor& left_drive() {
	static pros::Motor motor(LEFT_DRIVE_PORT);
	return motor;
}

pros::Motor& right_drive() {
	static pros::Motor motor(-RIGHT_DRIVE_PORT);
	return motor;
}

pros::Motor& arm_motor() {
	static pros::Motor motor(ARM_PORT);
	return motor;
}

pros::Motor& claw_motor() {
	static pros::Motor motor(CLAW_PORT);
	return motor;
}

pros::Controller& master() {
	static pros::Controller controller(pros::E_CONTROLLER_MASTER);
	return controller;
}

int clamp_int(int value, int lo, int hi) {
	if (value < lo) return lo;
	if (value > hi) return hi;
	return value;
}

int deadband(int value) {
	return std::abs(value) < JOYSTICK_DEADBAND ? 0 : value;
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

bool has_json_value(const std::string& line, const char* key, const char* value) {
	return contains(line, key) && contains(line, value);
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
	return drive_ready;
}

bool arm_port_ok() {
	return arm_ready;
}

bool claw_port_ok() {
	return claw_ready;
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

void configure_motors() {
	drive_ready = motor_port_present(LEFT_DRIVE_PORT) && motor_port_present(RIGHT_DRIVE_PORT);
	arm_ready = motor_port_present(ARM_PORT);
	claw_ready = motor_port_present(CLAW_PORT);
	if (drive_ports_ok()) {
		left_drive().set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
		right_drive().set_brake_mode(pros::E_MOTOR_BRAKE_BRAKE);
		left_drive().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
		right_drive().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
		left_drive().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
		right_drive().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
		left_drive().tare_position();
		right_drive().tare_position();
	}
	if (arm_port_ok()) {
		arm_motor().set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
		arm_motor().set_current_limit(ARM_CURRENT_LIMIT_MA);
		arm_motor().set_voltage_limit(ARM_VOLTAGE_LIMIT_MV);
	}
	if (claw_port_ok()) {
		claw_motor().set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
		claw_motor().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
		claw_motor().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
	}
}

void stop_all() {
	last_left_cmd = 0;
	last_right_cmd = 0;
	last_arm_cmd = 0;
	last_claw_cmd = 0;
	if (drive_ports_ok()) {
		left_drive().move(0);
		right_drive().move(0);
	}
	if (arm_port_ok()) arm_motor().move_velocity(0);
	if (claw_port_ok()) claw_motor().move_velocity(0);
}

std::string motor_sample_json(const char* device, const char* subsystem, pros::Motor& motor,
                              uint32_t sample_ms) {
	char buf[768];
	std::snprintf(
	    buf,
	    sizeof(buf),
	    "{\"device\":\"%s\",\"subsystem\":\"%s\",\"sample_ms\":%lu,"
	    "\"values\":{\"position_deg\":%.1f,\"velocity_rpm\":%.1f,"
	    "\"current_amp\":%.3f,\"power_w\":%.3f,\"torque_nm\":%.3f,"
	    "\"efficiency_pct\":%.1f,\"temperature_c\":%.1f}}",
	    device,
	    subsystem,
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
	std::string out = "[";
	bool first = true;
	if (drive_ports_ok()) {
		out += motor_sample_json("left_drive", "drivetrain", left_drive(), sample_ms);
		out += ",";
		out += motor_sample_json("right_drive", "drivetrain", right_drive(), sample_ms);
		first = false;
	}
	if (arm_port_ok()) {
		if (!first) out += ",";
		out += motor_sample_json("arm", "arm", arm_motor(), sample_ms);
		first = false;
	}
	if (claw_port_ok()) {
		if (!first) out += ",";
		out += motor_sample_json("claw", "claw", claw_motor(), sample_ms);
	}
	out += "]";
	return out;
}

void emit_ack(int seq, const char* state, const char* fault_json = "null") {
	emit_json(
	    "{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\",\"recv_ms\":%lu,"
	    "\"manual_mode\":true,\"drive_ports_ok\":%s,\"arm_port_ok\":%s,\"claw_port_ok\":%s,"
	    "\"estop\":%s,\"fault\":%s}",
	    seq,
	    state,
	    static_cast<unsigned long>(pros::millis()),
	    drive_ports_ok() ? "true" : "false",
	    arm_port_ok() ? "true" : "false",
	    claw_port_ok() ? "true" : "false",
	    estop_latched ? "true" : "false",
	    fault_json);
}

void emit_status(const char* state, const char* reason, const char* message) {
	emit_json(
	    "{\"v\":1,\"type\":\"bridge_status\",\"state\":\"%s\",\"reason\":\"%s\","
	    "\"message\":\"%s\",\"manual_mode\":true,\"observed_ms\":%lu}",
	    state,
	    reason,
	    message,
	    static_cast<unsigned long>(pros::millis()));
}

void emit_telemetry() {
	const uint32_t sample_ms = pros::millis();
	ControllerSnapshot snapshot;
	if (controller_mutex.take(20)) {
		snapshot = controller_snapshot;
		controller_mutex.give();
	}

	emit_json(
	    "{\"v\":1,\"type\":\"telemetry\",\"mode\":\"manual_driver\",\"manual_mode\":true,"
	    "\"t_ms\":%lu,\"battery_mv\":%ld,\"battery_current_ma\":%ld,\"battery_pct\":%.1f,"
	    "\"battery_temp_c\":%.1f,\"last_packet_age_ms\":%lu,\"estop\":%s,"
	    "\"drive_ports_ok\":%s,\"arm_port_ok\":%s,\"claw_port_ok\":%s,"
	    "\"motor_ports\":%s,\"left_cmd\":%d,\"right_cmd\":%d,\"arm_cmd\":%d,\"claw_cmd\":%d,"
	    "\"controller\":{\"left_y\":%d,\"right_x\":%d,\"l1\":%s,\"l2\":%s,"
	    "\"r1\":%s,\"r2\":%s,\"a\":%s,\"b\":%s,\"x\":%s,\"y\":%s},"
	    "\"left_pos_deg\":%.1f,\"right_pos_deg\":%.1f,"
	    "\"left_vel_rpm\":%.1f,\"right_vel_rpm\":%.1f,\"motor_samples\":%s}",
	    static_cast<unsigned long>(sample_ms),
	    static_cast<long>(pros::battery::get_voltage()),
	    static_cast<long>(pros::battery::get_current()),
	    pros::battery::get_capacity(),
	    pros::battery::get_temperature(),
	    static_cast<unsigned long>(sample_ms >= last_packet_ms ? sample_ms - last_packet_ms : 0),
	    estop_latched ? "true" : "false",
	    drive_ports_ok() ? "true" : "false",
	    arm_port_ok() ? "true" : "false",
	    claw_port_ok() ? "true" : "false",
	    motor_ports_json().c_str(),
	    last_left_cmd,
	    last_right_cmd,
	    last_arm_cmd,
	    last_claw_cmd,
	    snapshot.left_y,
	    snapshot.right_x,
	    snapshot.l1 ? "true" : "false",
	    snapshot.l2 ? "true" : "false",
	    snapshot.r1 ? "true" : "false",
	    snapshot.r2 ? "true" : "false",
	    snapshot.a ? "true" : "false",
	    snapshot.b ? "true" : "false",
	    snapshot.x ? "true" : "false",
	    snapshot.y ? "true" : "false",
	    drive_ports_ok() ? left_drive().get_position() : 0.0,
	    drive_ports_ok() ? right_drive().get_position() : 0.0,
	    drive_ports_ok() ? left_drive().get_actual_velocity() : 0.0,
	    drive_ports_ok() ? right_drive().get_actual_velocity() : 0.0,
	    motor_samples_json(sample_ms).c_str());
}

void handle_line(const std::string& line) {
	const int seq = extract_int_field(line, "seq");
	if (seq < 0) {
		emit_status("warn", "bad_packet", "manual telemetry received packet without integer seq");
		return;
	}

	last_packet_ms = pros::millis();

	if (has_json_value(line, "\"type\"", "\"heartbeat\"")) {
		emit_ack(seq, "ok");
		return;
	}

	if (!has_json_value(line, "\"type\"", "\"cmd\"")) {
		emit_ack(seq, "rejected", "\"malformed_json\"");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"stop\"")) {
		estop_latched = contains(line, "operator_estop");
		stop_all();
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"drive\"") ||
	    has_json_value(line, "\"cmd\"", "\"turn\"") ||
	    has_json_value(line, "\"cmd\"", "\"routine\"") ||
	    has_json_value(line, "\"cmd\"", "\"grab\"") ||
	    has_json_value(line, "\"cmd\"", "\"lift\"") ||
	    has_json_value(line, "\"cmd\"", "\"release\"")) {
		emit_ack(seq, "rejected", "\"manual_mode\"");
		return;
	}

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
		if (ch == '\r') continue;
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
			stop_all();
			emit_status("warn", "oversized_packet", "discarded serial packet above 2048 bytes");
		}
	}
}

void controller_task(void*) {
	while (true) {
		ControllerSnapshot snapshot;
		snapshot.left_y = deadband(master().get_analog(pros::E_CONTROLLER_ANALOG_LEFT_Y));
		snapshot.right_x = deadband(master().get_analog(pros::E_CONTROLLER_ANALOG_RIGHT_X));
		snapshot.l1 = master().get_digital(pros::E_CONTROLLER_DIGITAL_L1);
		snapshot.l2 = master().get_digital(pros::E_CONTROLLER_DIGITAL_L2);
		snapshot.r1 = master().get_digital(pros::E_CONTROLLER_DIGITAL_R1);
		snapshot.r2 = master().get_digital(pros::E_CONTROLLER_DIGITAL_R2);
		snapshot.a = master().get_digital(pros::E_CONTROLLER_DIGITAL_A);
		snapshot.b = master().get_digital(pros::E_CONTROLLER_DIGITAL_B);
		snapshot.x = master().get_digital(pros::E_CONTROLLER_DIGITAL_X);
		snapshot.y = master().get_digital(pros::E_CONTROLLER_DIGITAL_Y);

		if (controller_mutex.take(20)) {
			controller_snapshot = snapshot;
			controller_mutex.give();
		}

		if (estop_latched) {
			stop_all();
			pros::delay(CONTROL_MS);
			continue;
		}

		const int forward = snapshot.left_y;
		const int turn = snapshot.right_x;
		last_left_cmd = clamp_int(forward + turn, -DRIVE_POWER_LIMIT, DRIVE_POWER_LIMIT);
		last_right_cmd = clamp_int(forward - turn, -DRIVE_POWER_LIMIT, DRIVE_POWER_LIMIT);
		if (drive_ports_ok()) {
			left_drive().move(last_left_cmd);
			right_drive().move(last_right_cmd);
		}

		last_arm_cmd = 0;
		if (snapshot.r1) last_arm_cmd = ARM_RPM;
		if (snapshot.r2) last_arm_cmd = -ARM_RPM;
		if (arm_port_ok()) arm_motor().move_velocity(last_arm_cmd);

		last_claw_cmd = 0;
		if (snapshot.l1) last_claw_cmd = CLAW_RPM;
		if (snapshot.l2) last_claw_cmd = -CLAW_RPM;
		if (claw_port_ok()) claw_motor().move_velocity(last_claw_cmd);

		pros::delay(CONTROL_MS);
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
	configure_motors();

	pros::screen::set_pen(pros::c::COLOR_WHITE);
	pros::screen::print(pros::E_TEXT_LARGE, 1, "slot 7 driver telemetry");
	pros::screen::print(pros::E_TEXT_MEDIUM, 3, "manual controller owns drive");
	pros::screen::print(pros::E_TEXT_MEDIUM, 5, "ports L%d R%d A%d C%d",
	                    LEFT_DRIVE_PORT, RIGHT_DRIVE_PORT, ARM_PORT, CLAW_PORT);

	emit_status("ok", "driver_telemetry_ready", "slot 7 manual driver telemetry initialized");
}

void opcontrol() {
	pros::Task rx_task(receive_task, nullptr, "driver_rx");
	pros::Task control(controller_task, nullptr, "driver_control");
	pros::Task telemetry(telemetry_task, nullptr, "driver_telem");

	while (true) {
		pros::delay(1000);
	}
}

void disabled() {}
void autonomous() {}
void competition_initialize() {}
