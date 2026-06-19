// Starter sketch for the V5 Brain side of Vexy.
//
// This file is a bring-up guide, not yet proven against the physical Brain.
// Tomorrow's first task is to verify the exact PROS stream identifier behavior
// on the V5 user/console USB serial port, then wire these handlers to motors.

#include "main.h"
#include "pros/apix.h"
#include <cstdio>
#include <cstring>
#include <string>

namespace {
constexpr int WATCHDOG_MS = 250;
constexpr double MAX_LINEAR = 0.35;
constexpr double MAX_OMEGA = 0.60;

uint32_t last_packet_ms = 0;
bool estop = false;

double clamp(double value, double lo, double hi) {
  if (value < lo) return lo;
  if (value > hi) return hi;
  return value;
}

void stop_drive(const char* reason) {
  (void)reason;
  // TODO: set drivetrain motors to zero once ports are known.
}

void ack(int seq, const char* state, const char* fault = "null") {
  std::printf("{\"v\":1,\"ack\":%d,\"type\":\"ack\",\"state\":\"%s\",\"recv_ms\":%lu,\"fault\":%s}\n",
              seq, state, pros::millis(), fault);
  std::fflush(stdout);
}

int extract_seq(const std::string& line) {
  const std::string key = "\"seq\":";
  const auto pos = line.find(key);
  if (pos == std::string::npos) return -1;
  return std::atoi(line.c_str() + pos + key.size());
}

bool contains(const std::string& line, const char* needle) {
  return line.find(needle) != std::string::npos;
}

void handle_line(const std::string& line) {
  const int seq = extract_seq(line);
  last_packet_ms = pros::millis();

  if (contains(line, "\"type\":\"heartbeat\"")) {
    ack(seq, "ok");
    return;
  }

  if (contains(line, "\"cmd\":\"stop\"")) {
    estop = contains(line, "operator_estop");
    stop_drive("stop command");
    ack(seq, "ok");
    return;
  }

  if (contains(line, "\"cmd\":\"drive\"")) {
    if (estop) {
      stop_drive("estop latched");
      ack(seq, "rejected", "\"estop_latched\"");
      return;
    }

    // TODO: parse vx/vy/omega with a tiny JSON parser or fixed packet fields.
    // Keep parsing deliberately simple and reject on any ambiguity.
    const double vx = clamp(0.0, -MAX_LINEAR, MAX_LINEAR);
    const double omega = clamp(0.0, -MAX_OMEGA, MAX_OMEGA);
    (void)vx;
    (void)omega;

    // TODO: map vx/omega to drivetrain closed-loop command.
    ack(seq, "ok");
    return;
  }

  stop_drive("unknown command");
  ack(seq, "rejected", "\"unknown_command\"");
}
}  // namespace

void initialize() {
  // If reading serial ourselves, PROS docs recommend disabling COBS.
  serctl(SERCTL_DISABLE_COBS, nullptr);
  last_packet_ms = pros::millis();
}

void opcontrol() {
  std::string line;
  while (true) {
    int ch = std::getchar();
    if (ch != EOF) {
      if (ch == '\n') {
        handle_line(line);
        line.clear();
      } else if (line.size() < 512) {
        line.push_back(static_cast<char>(ch));
      } else {
        line.clear();
        stop_drive("oversized packet");
      }
    }

    if (pros::millis() - last_packet_ms > WATCHDOG_MS) {
      stop_drive("watchdog");
    }

    pros::delay(10);
  }
}

