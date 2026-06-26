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
constexpr int ARM_PORT = 8;
constexpr int RELEASE_MOTOR_PORT = 3;
constexpr int MAX_TTL_MS = 500;
constexpr int MAX_DRIVE_RPM = 45;
constexpr int MAX_TURN_RPM = 35;
constexpr int DRIVE_CURRENT_LIMIT_MA = 1500;
constexpr int DRIVE_VOLTAGE_LIMIT_MV = 6000;
// Positive manipulator velocity closes the claw on the current robot build.
constexpr int GRAB_RPM = 100;
constexpr int LIFT_RPM = 100;
// Negative manipulator velocity opens the claw.
constexpr int RELEASE_RPM = -100;
constexpr int DEFAULT_RELEASE_MS = 650;
constexpr int DEFAULT_GRAB_MS = 700;
constexpr int DEFAULT_LIFT_MS = 900;
constexpr int MAX_CLAW_MS = 1500;
constexpr double WHEEL_CIRCUMFERENCE_M = 0.319;  // 4 in wheel.
constexpr double TRACK_WIDTH_M = 0.28;
constexpr double DRIVE_FORWARD_SIGN = -1.0;
constexpr int ARM_CURRENT_LIMIT_MA = 1800;
constexpr int ARM_VOLTAGE_LIMIT_MV = 6000;
constexpr double ARM_UP_DEG = 300.0;
constexpr double ARM_TOL_DEG = 5.0;
constexpr int ARM_MOVE_RPM = 50;
constexpr int ARM_STALL_MA = 2000;
constexpr uint32_t ARM_STALL_HOLD_MS = 200;
constexpr uint32_t ARM_MOVE_TIMEOUT_MS = 3500;
constexpr uint32_t ROUTINE_720_SPIN_MS = 29000;
constexpr double ROUTINE_720_OMEGA_RAD_S = 0.45;
constexpr uint32_t ROUTINE_STEP_MS = 40;
constexpr int ROUTINE_DRIVE_TTL_MS = 180;
constexpr double ROUTINE_ONE_FOOT_M = 0.3048;
constexpr int ROUTINE_DRIVE_RPM = 25;
constexpr double ROUTINE_DRIVE_TOL_DEG = 8.0;
constexpr uint32_t ROUTINE_DRIVE_TIMEOUT_MS = 4500;

volatile uint32_t last_packet_ms = 0;
volatile uint32_t motion_until_ms = 0;
volatile bool estop_latched = false;
volatile bool watchdog_fault = false;
volatile int pending_routine_slot = 0;
volatile int active_routine_slot = 0;
volatile bool routine_active = false;
volatile bool routine_cancel_requested = false;

pros::Mutex stdout_mutex;

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
pros::Motor& release_motor() {
	static pros::Motor motor(RELEASE_MOTOR_PORT);
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

bool arm_port_ok() {
	return motor_port_present(ARM_PORT);
}

bool release_port_ok() {
	return motor_port_present(RELEASE_MOTOR_PORT);
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

void configure_arm() {
	if (!arm_port_ok()) return;
	arm_motor().set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
	arm_motor().set_current_limit(ARM_CURRENT_LIMIT_MA);
	arm_motor().set_voltage_limit(ARM_VOLTAGE_LIMIT_MV);
	arm_motor().tare_position();
}

void configure_release() {
	if (!release_port_ok()) return;
	release_motor().set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
	release_motor().set_current_limit(DRIVE_CURRENT_LIMIT_MA);
	release_motor().set_voltage_limit(DRIVE_VOLTAGE_LIMIT_MV);
	release_motor().tare_position();
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

void stop_arm(const char* reason) {
	(void)reason;
	if (!arm_port_ok()) return;
	arm_motor().move_velocity(0);
	arm_motor().brake();
}

void stop_all(const char* reason) {
	stop_drive(reason);
	stop_arm(reason);
}

void stop_release() {
	if (!release_port_ok()) return;
	release_motor().move_velocity(0);
	release_motor().brake();
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

void release_ball(int duration_ms) {
	if (duration_ms < 1) duration_ms = DEFAULT_RELEASE_MS;
	if (duration_ms > MAX_CLAW_MS) duration_ms = MAX_CLAW_MS;
	stop_drive("release command");
	release_motor().move_velocity(RELEASE_RPM);
	pros::delay(duration_ms);
	stop_release();
}

void run_claw_action(const char* reason, int rpm, int duration_ms, int default_duration_ms) {
	if (duration_ms < 1) duration_ms = default_duration_ms;
	if (duration_ms > MAX_CLAW_MS) duration_ms = MAX_CLAW_MS;
	stop_drive(reason);
	release_motor().move_velocity(rpm);
	pros::delay(duration_ms);
	stop_release();
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
	if (release_port_ok()) {
		if (!first) out += ",";
		out += motor_sample_json("effector_motor", "manipulator", release_motor(), sample_ms);
	}
	out += "]";
	return out;
}

bool routine_busy() {
	return routine_active || pending_routine_slot != 0;
}

const char* routine_slot_json(char* buf, size_t size) {
	const int slot = active_routine_slot;
	if (slot >= 2 && slot <= 4) {
		std::snprintf(buf, size, "%d", slot);
		return buf;
	}
	return "null";
}

void emit_ack(int seq, const char* state, const char* fault_json = "null") {
	char slot_buf[8];
	emit_json(
	    "{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\",\"recv_ms\":%lu,"
	    "\"battery_mv\":%ld,\"battery_pct\":%.1f,\"watchdog_age_ms\":%lu,"
	    "\"estop\":%s,\"motion_enabled\":%s,\"drive_ports_ok\":%s,\"arm_port_ok\":%s,"
	    "\"routine_active\":%s,\"routine_slot\":%s,\"motor_ports\":%s,"
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
	    arm_port_ok() ? "true" : "false",
	    routine_busy() ? "true" : "false",
	    routine_slot_json(slot_buf, sizeof(slot_buf)),
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
	char slot_buf[8];
	emit_json(
	    "{\"v\":1,\"type\":\"telemetry\",\"t_ms\":%lu,\"battery_mv\":%ld,"
	    "\"battery_current_ma\":%ld,\"battery_pct\":%.1f,\"battery_temp_c\":%.1f,"
	    "\"watchdog_age_ms\":%lu,\"motion_ttl_overrun_ms\":%lu,\"estop\":%s,"
	    "\"motion_enabled\":%s,\"drive_ports_ok\":%s,\"arm_port_ok\":%s,"
	    "\"routine_active\":%s,\"routine_slot\":%s,\"motor_ports\":%s,"
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
	    arm_port_ok() ? "true" : "false",
	    routine_busy() ? "true" : "false",
	    routine_slot_json(slot_buf, sizeof(slot_buf)),
	    motor_ports_json().c_str(),
	    drive_ports_ok() ? left_drive().get_position() : 0.0,
	    drive_ports_ok() ? right_drive().get_position() : 0.0,
	    drive_ports_ok() ? left_drive().get_actual_velocity() : 0.0,
	    drive_ports_ok() ? right_drive().get_actual_velocity() : 0.0,
	    motor_samples_json(sample_ms).c_str());
}

bool routine_guard_ok() {
	if (routine_cancel_requested || estop_latched) return false;
	if (packet_age_ms() > WATCHDOG_MS) return false;
	return true;
}

void routine_abort(const char* reason, const char* message) {
	stop_all(reason);
	emit_status("warn", reason, message);
}

bool routine_pause(uint32_t duration_ms) {
	const uint32_t start_ms = pros::millis();
	while (pros::millis() - start_ms < duration_ms) {
		if (!routine_guard_ok()) return false;
		pros::delay(ROUTINE_STEP_MS);
	}
	return true;
}

bool run_timed_turn(uint32_t duration_ms, double omega_rad_s) {
	const uint32_t start_ms = pros::millis();
	while (pros::millis() - start_ms < duration_ms) {
		if (!routine_guard_ok()) {
			routine_abort("routine_cancelled", "timed turn stopped before completion");
			return false;
		}
		set_drive(0.0, omega_rad_s, ROUTINE_DRIVE_TTL_MS);
		pros::delay(ROUTINE_STEP_MS);
	}
	stop_drive("routine turn complete");
	return true;
}

bool move_drive_relative(double distance_m) {
	if (!drive_ports_ok()) {
		routine_abort("not_assembled", "drive routine requires left/right drive motors");
		return false;
	}
	const double delta_deg = DRIVE_FORWARD_SIGN * distance_m / WHEEL_CIRCUMFERENCE_M * 360.0;
	const double left_target = left_drive().get_position() + delta_deg;
	const double right_target = right_drive().get_position() + delta_deg;
	const uint32_t start_ms = pros::millis();

	left_drive().move_absolute(left_target, ROUTINE_DRIVE_RPM);
	right_drive().move_absolute(right_target, ROUTINE_DRIVE_RPM);
	motion_until_ms = start_ms + ROUTINE_DRIVE_TIMEOUT_MS;

	while (pros::millis() - start_ms < ROUTINE_DRIVE_TIMEOUT_MS) {
		if (!routine_guard_ok()) {
			routine_abort("routine_cancelled", "drive routine stopped before completion");
			return false;
		}
		const double left_err = std::fabs(left_drive().get_position() - left_target);
		const double right_err = std::fabs(right_drive().get_position() - right_target);
		if (left_err <= ROUTINE_DRIVE_TOL_DEG && right_err <= ROUTINE_DRIVE_TOL_DEG) {
			stop_drive("drive target reached");
			return true;
		}
		pros::delay(ROUTINE_STEP_MS);
	}

	routine_abort("ttl_expired", "drive routine timed out before reaching encoder target");
	return false;
}

bool move_arm_absolute(double target_deg) {
	if (!arm_port_ok()) {
		routine_abort("not_assembled", "arm routine requires the arm motor on port 8");
		return false;
	}
	const uint32_t start_ms = pros::millis();
	uint32_t stall_since_ms = 0;
	arm_motor().move_absolute(target_deg, ARM_MOVE_RPM);

	while (pros::millis() - start_ms < ARM_MOVE_TIMEOUT_MS) {
		if (!routine_guard_ok()) {
			routine_abort("routine_cancelled", "arm routine stopped before completion");
			return false;
		}

		const double err = std::fabs(arm_motor().get_position() - target_deg);
		if (err <= ARM_TOL_DEG) {
			arm_motor().brake();
			return true;
		}

		const int current_ma = arm_motor().get_current_draw();
		if (current_ma >= ARM_STALL_MA) {
			if (stall_since_ms == 0) {
				stall_since_ms = pros::millis();
			} else if (pros::millis() - stall_since_ms >= ARM_STALL_HOLD_MS) {
				routine_abort("ttl_expired", "arm routine hit a sustained current limit");
				return false;
			}
		} else {
			stall_since_ms = 0;
		}
		pros::delay(ROUTINE_STEP_MS);
	}

	routine_abort("ttl_expired", "arm routine timed out before reaching target");
	return false;
}

bool run_routine_slot(int slot) {
	active_routine_slot = slot;
	routine_active = true;
	routine_cancel_requested = false;
	emit_status("ok", "routine_started", "Brain routine slot started");

	bool ok = false;
	if (slot == 2) {
		ok = run_timed_turn(ROUTINE_720_SPIN_MS, ROUTINE_720_OMEGA_RAD_S);
	} else if (slot == 3) {
		ok = move_arm_absolute(ARM_UP_DEG) && routine_pause(500) && move_arm_absolute(0.0);
	} else if (slot == 4) {
		ok = move_drive_relative(ROUTINE_ONE_FOOT_M) && routine_pause(500) &&
		     move_drive_relative(-ROUTINE_ONE_FOOT_M);
	}

	stop_all("routine finished");
	emit_status(ok ? "ok" : "warn",
	            ok ? "routine_finished" : "routine_aborted",
	            ok ? "Brain routine slot completed" : "Brain routine slot stopped early");
	routine_active = false;
	active_routine_slot = 0;
	routine_cancel_requested = false;
	return ok;
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
		stop_all("unknown packet type");
		emit_ack(seq, "rejected", "\"malformed_json\"");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"stop\"")) {
		estop_latched = contains(line, "operator_estop");
		routine_cancel_requested = true;
		pending_routine_slot = 0;
		stop_all("stop command");
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"drive\"") ||
	    has_json_value(line, "\"cmd\"", "\"turn\"")) {
		if (routine_busy()) {
			emit_ack(seq, "rejected", "\"busy\"");
			return;
		}
		if (estop_latched) {
			stop_all("estop latched");
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (!drive_ports_ok()) {
			stop_all("drive ports missing");
			emit_ack(seq, "rejected", "\"not_assembled\"");
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

	if (has_json_value(line, "\"cmd\"", "\"routine\"")) {
		if (estop_latched) {
			stop_all("estop latched");
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (routine_busy()) {
			emit_ack(seq, "rejected", "\"busy\"");
			return;
		}

		const int slot = extract_int_field(line, "slot");
		if (slot < 2 || slot > 4) {
			emit_ack(seq, "rejected", "\"out_of_range\"");
			return;
		}
		if ((slot == 2 || slot == 4) && !drive_ports_ok()) {
			stop_all("routine drive ports missing");
			emit_ack(seq, "rejected", "\"not_assembled\"");
			return;
		}
		if (slot == 3 && !arm_port_ok()) {
			stop_all("routine arm port missing");
			emit_ack(seq, "rejected", "\"not_assembled\"");
			return;
		}

		routine_cancel_requested = false;
		pending_routine_slot = slot;
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"arm\"")) {
		if (routine_busy()) {
			emit_ack(seq, "rejected", "\"busy\"");
			return;
		}
		if (estop_latched) {
			stop_all("estop latched");
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (!arm_port_ok()) {
			stop_all("arm port missing");
			emit_ack(seq, "rejected", "\"not_assembled\"");
			return;
		}

		const double target_deg = clamp(extract_double_field(line, "target_deg"), 0.0, 360.0);
		stop_drive("arm command");
		arm_motor().move_absolute(target_deg, ARM_MOVE_RPM);
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"release\"")) {
		if (estop_latched) {
			stop_drive("estop latched");
			stop_release();
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (!release_port_ok()) {
			stop_drive("release port missing");
			emit_ack(seq, "rejected", "\"release_port_missing\"");
			return;
		}

		int duration_ms = extract_int_field(line, "duration_ms", DEFAULT_RELEASE_MS);
		if (duration_ms < 1) duration_ms = DEFAULT_RELEASE_MS;
		if (duration_ms > MAX_CLAW_MS) duration_ms = MAX_CLAW_MS;
		release_ball(duration_ms);
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"grab\"") ||
	    has_json_value(line, "\"cmd\"", "\"lift\"")) {
		if (estop_latched) {
			stop_drive("estop latched");
			stop_release();
			emit_ack(seq, "rejected", "\"estop_latched\"");
			return;
		}
		if (!release_port_ok()) {
			stop_drive("release port missing");
			emit_ack(seq, "rejected", "\"release_port_missing\"");
			return;
		}

		const bool is_lift = has_json_value(line, "\"cmd\"", "\"lift\"");
		const int default_duration_ms = is_lift ? DEFAULT_LIFT_MS : DEFAULT_GRAB_MS;
		const int rpm = is_lift ? LIFT_RPM : GRAB_RPM;
		int duration_ms = extract_int_field(line, "duration_ms", default_duration_ms);
		run_claw_action(is_lift ? "lift command" : "grab command", rpm, duration_ms,
		                default_duration_ms);
		emit_ack(seq, "ok");
		return;
	}

	if (has_json_value(line, "\"cmd\"", "\"set_goal\"")) {
		stop_drive("set_goal not handled by Brain");
		emit_ack(seq, "rejected", "\"unsupported_goal\"");
		return;
	}

	stop_all("unknown command");
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
			routine_cancel_requested = true;
			stop_all("oversized packet");
			emit_status("warn", "oversized_packet", "discarded serial packet above 2048 bytes");
		}
	}
}

void routine_task(void*) {
	while (true) {
		const int slot = pending_routine_slot;
		if (slot != 0 && !routine_active) {
			pending_routine_slot = 0;
			run_routine_slot(slot);
		}
		pros::delay(20);
	}
}

void watchdog_task(void*) {
	while (true) {
		if (packet_age_ms() > WATCHDOG_MS) {
			routine_cancel_requested = true;
			stop_all("watchdog");
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
	configure_release();

	pros::screen::set_pen(pros::c::COLOR_WHITE);
	pros::screen::print(pros::E_TEXT_LARGE, 1, "vexy serial bridge");
	pros::screen::print(pros::E_TEXT_MEDIUM, 3, "guarded ports %d/%d release %d",
	                    LEFT_DRIVE_PORT, RIGHT_DRIVE_PORT, RELEASE_MOTOR_PORT);

	emit_status("ok", "brain_bridge_ready", "guarded ack/telemetry bridge initialized");
}

void opcontrol() {
	pros::Task rx_task(receive_task, nullptr, "vex_rx");
	pros::Task routines(routine_task, nullptr, "vex_routines");
	pros::Task watchdog(watchdog_task, nullptr, "vex_watchdog");
	pros::Task telemetry(telemetry_task, nullptr, "vex_telem");

	while (true) {
		pros::delay(1000);
	}
}

void disabled() {}
void autonomous() {}
void competition_initialize() {}
