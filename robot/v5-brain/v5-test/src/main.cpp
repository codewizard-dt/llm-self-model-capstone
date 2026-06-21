#include "main.h"
#include "pros/apix.h"
#include "pros/motors.hpp"
#include "pros/screen.hpp"
#include <cstdio>

// ---------------------------------------------------------------------------
// V5 arm-raise telemetry test.
//
// Runs N_CYCLES episodes of: raise the arm (Smart Port 8) while streaming dense
// telemetry over USB, then lower + pause QUIETLY. Telemetry is emitted ONLY
// during the raise so the Pi sees clean per-episode bursts separated by silence.
//
// Built as a MONOLITH (USE_PACKAGE:=0). COBS is DISABLED so the Pi reads plain
// newline-delimited JSON via pyserial. (Consequence: `pros terminal` will not
// decode this output — verify with a raw serial read instead.)
// ---------------------------------------------------------------------------

namespace {
constexpr int8_t   ARM_PORT        = 8;       // Clawbot arm Smart Port
constexpr double   RAISE_DEG        = 300.0;  // motor deg to raise (~43 deg at arm, 7:1).
                                              // + assumed = up; FLIP sign if it lowers.
constexpr int32_t  MOVE_VEL_RPM     = 50;     // gentle raise speed (motor RPM)
constexpr int32_t  LOWER_VEL_RPM    = 50;     // return-to-rest speed
constexpr int      N_CYCLES         = 5;
constexpr uint32_t SAMPLE_MS        = 10;     // 100 Hz telemetry during the action
constexpr uint32_t MOVE_TIMEOUT_MS  = 3000;   // backstop so a stall can't hang a cycle
constexpr double   REACH_TOL_DEG    = 5.0;    // "reached target" tolerance
constexpr int32_t  STALL_MA         = 2000;   // sustained current => treat as end-stop
constexpr uint32_t STALL_HOLD_MS    = 200;
constexpr uint32_t PAUSE_MS         = 1000;   // quiet gap between cycles

// Stream the raise for one episode, sampling at SAMPLE_MS cadence.
void raise_with_telemetry(pros::Motor& arm, int ep) {
	const uint32_t t0 = pros::millis();
	const double   temp_c  = arm.get_temperature();
	const int32_t  volt_mv = arm.get_voltage();

	std::printf("{\"event\":\"raise_start\",\"ep\":%d,\"t\":%lu,\"tgt_deg\":%.0f,"
	            "\"vel_rpm\":%ld,\"temp_c\":%.0f,\"volt_mv\":%ld}\n",
	            ep, (unsigned long)t0, RAISE_DEG, (long)MOVE_VEL_RPM,
	            temp_c, (long)volt_mv);
	std::fflush(stdout);

	arm.move_absolute(RAISE_DEG, MOVE_VEL_RPM);

	int32_t  peak_cur = 0;
	int      samples  = 0;
	uint32_t stall_since = 0;          // 0 = not currently over threshold
	const char* fault = "null";
	bool reached = false;
	double pos = 0.0;
	uint32_t now = pros::millis();

	while (true) {
		pos                 = arm.get_position();
		const double  vel   = arm.get_actual_velocity();
		const int32_t cur   = arm.get_current_draw();
		const double  trq   = arm.get_torque();
		const uint32_t t    = pros::millis();

		std::printf("{\"t\":%lu,\"pos\":%.1f,\"vel\":%.0f,\"cur\":%ld,\"trq\":%.2f}\n",
		            (unsigned long)t, pos, vel, (long)cur, trq);
		std::fflush(stdout);

		if (cur > peak_cur) peak_cur = cur;
		samples++;

		// stall detection: current sustained at/above threshold
		if (cur >= STALL_MA) {
			if (stall_since == 0) stall_since = t;
			else if (t - stall_since > STALL_HOLD_MS) { fault = "\"stall\""; break; }
		} else {
			stall_since = 0;
		}

		const double err = pos - RAISE_DEG;
		if ((err < 0 ? -err : err) <= REACH_TOL_DEG) { reached = true; break; }
		if (t - t0 > MOVE_TIMEOUT_MS) { fault = "\"timeout\""; break; }

		pros::c::task_delay_until(&now, SAMPLE_MS);
	}

	if (fault[0] != 'n') arm.brake();   // stop holding on stall/timeout

	const uint32_t dur = pros::millis() - t0;
	std::printf("{\"event\":\"raise_end\",\"ep\":%d,\"t\":%lu,\"pos_deg\":%.1f,"
	            "\"reached\":%s,\"fault\":%s,\"dur_ms\":%lu,\"peak_cur_ma\":%ld,"
	            "\"samples\":%d}\n",
	            ep, (unsigned long)pros::millis(), pos, reached ? "true" : "false",
	            fault, (unsigned long)dur, (long)peak_cur, samples);
	std::fflush(stdout);

	pros::screen::print(pros::E_TEXT_MEDIUM, 4, "ep %d: pos %.0f reached=%d   ",
	                    ep, pos, reached ? 1 : 0);
}

// Lower back to rest, no telemetry (intentional silence between episodes).
void move_quietly(pros::Motor& arm, double target, int32_t vel) {
	const uint32_t t0 = pros::millis();
	arm.move_absolute(target, vel);
	while (true) {
		const double err = arm.get_position() - target;
		if ((err < 0 ? -err : err) <= REACH_TOL_DEG) break;
		if (pros::millis() - t0 > MOVE_TIMEOUT_MS) break;
		pros::delay(10);
	}
}
}  // namespace

void initialize() {
	// Raw newline-delimited JSON for the Pi (NOT COBS / pros terminal).
	pros::c::serctl(SERCTL_DISABLE_COBS, nullptr);

	pros::Motor arm(ARM_PORT);
	arm.set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
	arm.tare_position();

	pros::screen::set_pen(pros::c::COLOR_WHITE);
	pros::screen::print(pros::E_TEXT_LARGE, 1, "arm-telemetry test");
}

void opcontrol() {
	pros::Motor arm(ARM_PORT);
	arm.set_brake_mode(pros::E_MOTOR_BRAKE_HOLD);
	arm.tare_position();

	for (int ep = 1; ep <= N_CYCLES; ep++) {
		raise_with_telemetry(arm, ep);
		move_quietly(arm, 0.0, LOWER_VEL_RPM);   // lower (silent)
		pros::delay(PAUSE_MS);                    // pause (silent)
	}

	std::printf("{\"event\":\"run_done\",\"cycles\":%d,\"t\":%lu}\n",
	            N_CYCLES, (unsigned long)pros::millis());
	std::fflush(stdout);

	pros::screen::print(pros::E_TEXT_MEDIUM, 6, "run done (%d cycles)", N_CYCLES);
	while (true) pros::delay(1000);
}

void disabled() {}
void autonomous() {}
void competition_initialize() {}
