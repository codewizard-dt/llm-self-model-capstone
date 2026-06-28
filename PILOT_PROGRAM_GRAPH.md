# Pilot Online Task Loop Program Graph

Source program:

- Requirements: `.ai-sdd/programs/pilot-online-task-loop/requirements.md`
- Pipeline: `.ai-sdd/programs/pilot-online-task-loop/pipeline.yaml`

Generated from:

```bash
ai-sdd graph .ai-sdd/programs/pilot-online-task-loop
```

```mermaid
flowchart TD
    pilot_schemas["pilot-schemas<br/>slice [contracts] @215eight"]
    pm1_schemas_ready["pm1-schemas-ready<br/>milestone-gate @215eight"]
    observation_builder["observation-builder<br/>slice [pilot] @215eight"]
    skill_registry["skill-registry<br/>slice [pilot] @215eight"]
    llm_decision_adapter["llm-decision-adapter<br/>slice [pilot] @215eight"]
    safety_validator["safety-validator<br/>slice [pilot] @David"]
    ros_skill_executor["ros-skill-executor<br/>slice [pilot] @David"]
    assertion_engine["assertion-engine<br/>slice [pilot] @David"]
    run_logger["run-logger<br/>slice [pilot] @David"]
    pm3_live_observation["pm3-live-observation<br/>milestone-gate @215eight"]
    replay_mode["replay-mode<br/>slice [pilot] @David"]
    pm2_replay_loop["pm2-replay-loop<br/>milestone-gate @David"]
    pm4_one_skill_execution["pm4-one-skill-execution<br/>milestone-gate @David"]
    skill_baseline_capture["skill-baseline-capture<br/>slice [pilot] @David"]
    pm5_skill_baselines["pm5-skill-baselines<br/>milestone-gate @David"]
    delivery_recipe["delivery-recipe<br/>slice [pilot] @David"]
    pm6_delivery_loop_replay["pm6-delivery-loop-replay<br/>milestone-gate @David"]
    supervised_hardware_run["supervised-hardware-run<br/>slice [pilot] @David"]
    pm7_supervised_delivery_run["pm7-supervised-delivery-run<br/>milestone-gate @David"]
    generalized_recipes["generalized-recipes<br/>slice [pilot] @David"]
    pm8_expansion_proof["pm8-expansion-proof<br/>milestone-gate @David"]
    pilot_schemas --> pm1_schemas_ready
    pm1_schemas_ready --> observation_builder
    pm1_schemas_ready --> skill_registry
    observation_builder --> llm_decision_adapter
    skill_registry --> llm_decision_adapter
    skill_registry --> safety_validator
    safety_validator --> ros_skill_executor
    observation_builder --> assertion_engine
    llm_decision_adapter --> run_logger
    ros_skill_executor --> run_logger
    assertion_engine --> run_logger
    observation_builder --> pm3_live_observation
    llm_decision_adapter --> replay_mode
    assertion_engine --> replay_mode
    run_logger --> replay_mode
    replay_mode --> pm2_replay_loop
    ros_skill_executor --> pm4_one_skill_execution
    pm4_one_skill_execution --> skill_baseline_capture
    assertion_engine --> skill_baseline_capture
    run_logger --> skill_baseline_capture
    skill_baseline_capture --> pm5_skill_baselines
    pm5_skill_baselines --> delivery_recipe
    delivery_recipe --> pm6_delivery_loop_replay
    pm6_delivery_loop_replay --> supervised_hardware_run
    supervised_hardware_run --> pm7_supervised_delivery_run
    pm7_supervised_delivery_run --> generalized_recipes
    generalized_recipes --> pm8_expansion_proof
```
