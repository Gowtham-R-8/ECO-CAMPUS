import numpy as np
from backend.config import Config

class WhatIfSimulator:
    ACTION_PRESETS = {
        "reduce_ac_1h": {
            "name": "Reduce AC Operation by 1 hour/day",
            "resource": "electricity",
            "kwh_reduction_pct": 10.5,
            "water_reduction_pct": 0.0,
            "base_duration": 1.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 5.2
        },
        "reduce_ac_2h": {
            "name": "Reduce AC Operation by 2 hours/day",
            "resource": "electricity",
            "kwh_reduction_pct": 19.8,
            "water_reduction_pct": 0.0,
            "base_duration": 2.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 8.4
        },
        "adjust_thermostat": {
            "name": "Increase AC Cooling Setpoint (+2.0°C)",
            "resource": "electricity",
            "kwh_reduction_pct": 14.0,
            "water_reduction_pct": 0.0,
            "base_duration": 8.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 6.8
        },
        "weather_fluctuation": {
            "name": "Ambient Weather Fluctuation (Inspect Temperature Rise / Drop)",
            "resource": "electricity",
            "kwh_reduction_pct": 0.0,
            "water_reduction_pct": 0.0,
            "base_duration": 8.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 0.0
        },
        "heatwave_surge": {
            "name": "Ambient Weather Fluctuation (Inspect Temperature Rise / Drop)",
            "resource": "electricity",
            "kwh_reduction_pct": 0.0,
            "water_reduction_pct": 0.0,
            "base_duration": 8.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 0.0
        },
        "overcooling_drift": {
            "name": "Aggressive Overcooling (Thermostat forced down to 18°C)",
            "resource": "electricity",
            "kwh_reduction_pct": -25.0,
            "water_reduction_pct": 0.0,
            "base_duration": 8.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": -12.0
        },
        "optimize_lighting": {
            "name": "Smart Motion-Zoned Lighting & Daylight Harvesting",
            "resource": "electricity",
            "kwh_reduction_pct": 8.5,
            "water_reduction_pct": 0.0,
            "base_duration": 10.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 4.5
        },
        "fix_water_leak": {
            "name": "Isolate Main Valve Breach & Repair Flush Cisterns",
            "resource": "water",
            "kwh_reduction_pct": 1.5, # pumping energy
            "water_reduction_pct": 32.0,
            "base_duration": 24.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 7.5
        },
        "low_flow_aerators": {
            "name": "Install High-Efficiency Aeration Faucets (4 L/min)",
            "resource": "water",
            "kwh_reduction_pct": 2.0,
            "water_reduction_pct": 22.5,
            "base_duration": 24.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 6.0
        },
        "solar_pv_integration": {
            "name": "Integrate 50 kW Rooftop Solar PV Microgeneration",
            "resource": "electricity",
            "kwh_reduction_pct": 28.0,
            "water_reduction_pct": 0.0,
            "base_duration": 6.0,
            "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
            "sustainability_boost": 12.0
        }
    }

    @classmethod
    def simulate_action(cls, building_data, action_key_or_name, duration_hours=1.0, occupancy_multiplier=1.0, temperature=30.0):
        """
        Runs mathematical what-if simulation model factoring in:
        1. Ambient outdoor temperature heat penalty (cooling load surges by 5.2%/°C above 25°C, compressor COP drops).
        2. Intervention action consequences (energy reduction or surge).
        3. Real financial loss & wastage diagnostics when ambient temperature rises.
        """
        # Find matching preset
        preset = None
        for k, v in cls.ACTION_PRESETS.items():
            if k == action_key_or_name or v["name"].lower() == action_key_or_name.lower():
                preset = v
                break
        
        if not preset:
            # Generic customizable fallback
            preset = {
                "name": action_key_or_name,
                "resource": "electricity",
                "kwh_reduction_pct": min(35.0, 8.0 * float(duration_hours)),
                "water_reduction_pct": 0.0,
                "base_duration": float(duration_hours),
                "cost_per_kwh": Config.ELECTRICITY_COST_PER_KWH,
                "sustainability_boost": min(10.0, 4.0 + float(duration_hours) * 1.5)
            }

        # Nominal reference baseline values (measured at standard design comfort: 25.0°C)
        baseline_energy = float(building_data.get("current_energy", 1200.0))
        baseline_water = float(building_data.get("current_water", 18000.0))

        # -------------------------------------------------------------
        # 1. THERMODYNAMIC AMBIENT TEMPERATURE IMPACT (HEAT LOSS VS COOLING PROFIT)
        # -------------------------------------------------------------
        # Reference equilibrium comfort setpoint: 25.0°C (ASHRAE / Indian GRIHA benchmark)
        ref_temp = 25.0
        temp_val = float(temperature)
        delta_temp = round(temp_val - ref_temp, 1)

        if delta_temp > 0:
            # AMBIENT HEAT SURGE (HOTTER OUTDOOR WEATHER)
            # For every 1°C ambient rise above 25°C, cooling thermal load increases by 5.2%
            # (envelope conduction, solar insolation, air infiltration).
            # Chiller/compressor COP degrades by 2.4% per °C rise due to elevated head pressure.
            is_cool_bonus = False
            heat_penalty_pct = round(delta_temp * 5.2, 1)
            cop_degradation_pct = round(min(45.0, delta_temp * 2.4), 1)
            cop_boost_pct = 0.0
            cool_bonus_pct = 0.0

            # HVAC accounts for ~60% of total commercial/campus facility electrical demand
            thermal_loss_kwh = round((baseline_energy * 0.60) * (heat_penalty_pct / 100.0), 1)
            thermal_loss_cost_daily = round(thermal_loss_kwh * Config.ELECTRICITY_COST_PER_KWH, 2)
            thermal_loss_cost_monthly = round(thermal_loss_cost_daily * 30.0, 2)
            thermal_loss_cost_annual = round(thermal_loss_cost_daily * 365.0, 2)

            thermal_saving_kwh = 0.0
            thermal_saving_cost_daily = 0.0
            thermal_saving_cost_monthly = 0.0
            thermal_saving_cost_annual = 0.0

            # Weather-adjusted baseline before intervention under this ambient temperature
            effective_baseline_energy = round(baseline_energy + thermal_loss_kwh, 1)

        elif delta_temp < 0:
            # AMBIENT COOLING BONUS (COOLER OUTDOOR WEATHER)
            # When ambient outdoor temperature drops below 25°C, cooling load drops by 5.2%/°C
            # (natural economizer effect, reduced conductive thermal envelope gain).
            # Compressor COP improves by 2.8%/°C due to reduced condensing head pressure.
            is_cool_bonus = True
            cool_delta = abs(delta_temp)
            cool_bonus_pct = round(min(75.0, cool_delta * 5.2), 1)
            cop_boost_pct = round(min(45.0, cool_delta * 2.8), 1)
            cop_degradation_pct = 0.0
            heat_penalty_pct = 0.0

            thermal_loss_kwh = 0.0
            thermal_loss_cost_daily = 0.0
            thermal_loss_cost_monthly = 0.0
            thermal_loss_cost_annual = 0.0

            # Natural electricity savings and financial profit delivered by cool outdoor weather
            thermal_saving_kwh = round((baseline_energy * 0.60) * (cool_bonus_pct / 100.0), 1)
            thermal_saving_cost_daily = round(thermal_saving_kwh * Config.ELECTRICITY_COST_PER_KWH, 2)
            thermal_saving_cost_monthly = round(thermal_saving_cost_daily * 30.0, 2)
            thermal_saving_cost_annual = round(thermal_saving_cost_daily * 365.0, 2)

            # Weather-adjusted baseline before intervention under this cool ambient temperature
            effective_baseline_energy = round(max(0.0, baseline_energy - thermal_saving_kwh), 1)

        else:
            # OPTIMAL EQUILIBRIUM (25.0°C DESIGN COMFORT)
            is_cool_bonus = False
            heat_penalty_pct = 0.0
            cop_degradation_pct = 0.0
            cop_boost_pct = 0.0
            cool_bonus_pct = 0.0
            thermal_loss_kwh = 0.0
            thermal_loss_cost_daily = 0.0
            thermal_loss_cost_monthly = 0.0
            thermal_loss_cost_annual = 0.0
            thermal_saving_kwh = 0.0
            thermal_saving_cost_daily = 0.0
            thermal_saving_cost_monthly = 0.0
            thermal_saving_cost_annual = 0.0
            effective_baseline_energy = baseline_energy

        # -------------------------------------------------------------
        # 2. INTERVENTION ACTION IMPACT
        # -------------------------------------------------------------
        is_hvac_action = preset.get("resource") == "electricity" and any(
            term in preset["name"].lower() for term in ["ac", "cooling", "thermostat", "setpoint", "heatwave", "overcooling", "weather"]
        )

        base_dur = max(1.0, preset["base_duration"])
        applied_dur = min(float(duration_hours), 24.0)
        action_pct = preset["kwh_reduction_pct"] * (applied_dur / base_dur)

        if is_hvac_action:
            # Action acts on the HVAC portion of the weather-adjusted load
            action_saved_kwh = round((effective_baseline_energy * 0.60) * (action_pct / 100.0), 1)
        elif preset.get("resource") == "electricity":
            # Non-HVAC electricity action (lighting, rooftop solar)
            action_saved_kwh = round(baseline_energy * (action_pct / 100.0), 1)
        else:
            action_saved_kwh = 0.0

        # Simulated final energy consumption under this ambient temperature
        simulated_energy = round(max(0.0, effective_baseline_energy - action_saved_kwh), 1)

        # Water savings
        water_pct = preset["water_reduction_pct"]
        water_saved = round(baseline_water * (water_pct / 100.0), 1)
        simulated_water = round(baseline_water - water_saved, 1)
        cost_saved_water = round((water_saved / 1000.0) * Config.WATER_COST_PER_1000L, 2)

        # -------------------------------------------------------------
        # 3. ACTION SAVINGS & NET BOTTOM LINE FINANCIAL OUTCOME
        # -------------------------------------------------------------
        # Direct savings generated by the intervention action alone
        action_cost_saved_daily = round(action_saved_kwh * Config.ELECTRICITY_COST_PER_KWH + cost_saved_water, 2)
        action_monthly_saving = round(action_cost_saved_daily * 30.0, 2)
        action_annual_saving = round(action_cost_saved_daily * 365.0, 2)

        # Net balance comparison against nominal 25°C design baseline
        net_energy_diff = round(simulated_energy - baseline_energy, 1)
        net_financial_diff_daily = round(net_energy_diff * Config.ELECTRICITY_COST_PER_KWH - cost_saved_water, 2)
        net_annual_outcome = round(-net_financial_diff_daily * 365.0, 2)
        net_daily_outcome = round(-net_financial_diff_daily, 2)

        is_net_loss = (net_energy_diff > 0.0) or (net_financial_diff_daily > 0.0)

        if is_net_loss:
            # Ambient heat surge exceeds action savings -> Net Deficit
            status_text = "NET FINANCIAL LOSS"
            net_financial_loss_daily = net_financial_diff_daily
            net_financial_loss_monthly = round(net_financial_loss_daily * 30.0, 2)
            net_financial_loss_annual = round(net_financial_loss_daily * 365.0, 2)
            net_cost_saved_daily = 0.0
            net_annual_saving = 0.0
            net_energy_waste_daily = net_energy_diff
            sustainability_impact = -round(min(12.0, max(1.5, net_energy_diff / 45.0)), 1)
            monthly_co2_kg = round(net_energy_diff * Config.CO2_KG_PER_KWH * 30.0, 1)
            annual_co2_tons = round((monthly_co2_kg * 12.0) / 1000.0, 2)

            # Preserve intervention action savings for visibility side-by-side
            energy_saved = round(action_saved_kwh, 1)
            cost_saved_daily = action_cost_saved_daily
            monthly_saving = action_monthly_saving
            annual_saving = net_annual_outcome
        else:
            # Energy consumption drops below nominal baseline -> Net Savings Achieved
            status_text = "WEATHER COOLING PROFIT & SURPLUS" if is_cool_bonus else "NET SAVINGS ACHIEVED"
            net_financial_loss_daily = 0.0
            net_financial_loss_monthly = 0.0
            net_financial_loss_annual = 0.0
            net_energy_waste_daily = 0.0
            net_cost_saved_daily = round(abs(net_financial_diff_daily), 2)
            net_annual_saving = round(net_cost_saved_daily * 365.0, 2)

            # Combined energy saved and total cost saved (Action + Weather Cooling Bonus)
            energy_saved = round(abs(net_energy_diff), 1)
            cost_saved_daily = net_cost_saved_daily
            monthly_saving = round(cost_saved_daily * 30.0, 2)
            annual_saving = net_annual_saving

            sustainability_base = preset["sustainability_boost"] if preset["sustainability_boost"] != 0 else 5.0
            sustainability_impact = round(max(1.0, min(15.0, sustainability_base + (abs(delta_temp) * 0.8 if is_cool_bonus else 0.0))), 1)
            monthly_co2_kg = round(energy_saved * Config.CO2_KG_PER_KWH * 30.0, 1)
            annual_co2_tons = round((monthly_co2_kg * 12.0) / 1000.0, 2)

        # -------------------------------------------------------------
        # 4. HOURLY 24H SIMULATION CURVE (Thermal Diurnal Shape)
        # -------------------------------------------------------------
        hourly_before = []
        hourly_after = []
        labels = []

        for h in range(24):
            labels.append(f"{h:02d}:00")
            hour_mult = 0.35 if (h < 7 or h > 20) else (1.15 if 10 <= h <= 16 else 0.8)
            h_nom = (baseline_energy / 24.0) * hour_mult

            # Daytime heat bell curve peaking at 14:00
            if 8 <= h <= 18:
                if thermal_loss_kwh > 0:
                    heat_bell = float(np.sin((h - 8) / 10.0 * np.pi))
                    h_heat = (thermal_loss_kwh / 7.0) * heat_bell
                else:
                    h_heat = 0.0

                if thermal_saving_kwh > 0:
                    cool_bell = float(np.sin((h - 8) / 10.0 * np.pi))
                    h_cool = (thermal_saving_kwh / 7.0) * cool_bell
                else:
                    h_cool = 0.0
            else:
                h_heat = 0.0
                h_cool = 0.0

            h_before = float(round(h_nom + h_heat, 1))

            # Apply action reduction and cool weather load reduction
            if 8 <= h <= 18:
                h_red = float(action_saved_kwh / 11.0) if action_saved_kwh != 0 else 0.0
                h_sim = float(max(0.0, round(h_nom + h_heat - h_cool - h_red, 1)))
            else:
                h_sim = float(max(0.0, round(h_nom - h_cool, 1)))

            hourly_before.append(h_before)
            hourly_after.append(h_sim)

        # Comprehensive dual-sided loss and profit calculations
        daily_consumption_cost = round(simulated_energy * Config.ELECTRICITY_COST_PER_KWH + cost_saved_water, 2)
        annual_consumption_cost = round(daily_consumption_cost * 365.0, 2)
        daily_waste_loss = round((simulated_energy * 0.20) * Config.ELECTRICITY_COST_PER_KWH, 2)
        annual_waste_loss = round(daily_waste_loss * 365.0, 2)

        total_daily_profit = round(action_cost_saved_daily + (thermal_saving_cost_daily if is_cool_bonus else 0.0), 2)
        total_annual_profit = round(total_daily_profit * 365.0, 2)
        total_saved_kwh = round(action_saved_kwh + (thermal_saving_kwh if is_cool_bonus else 0.0), 1)

        if delta_temp > 0:
            total_daily_loss = round(thermal_loss_cost_daily, 2)
            total_annual_loss = round(thermal_loss_cost_annual, 2)
        else:
            total_daily_loss = round(daily_waste_loss, 2)
            total_annual_loss = round(annual_waste_loss, 2)

        return {
            "action_name": preset["name"],
            "duration_hours": duration_hours,
            "baseline_energy": round(baseline_energy, 1),
            "effective_baseline_energy": effective_baseline_energy,
            "simulated_energy": round(simulated_energy, 1),
            "energy_saved": round(energy_saved, 1),
            "action_saved_kwh": round(action_saved_kwh, 1),
            "action_cost_saved_daily": round(action_cost_saved_daily, 2),
            "action_monthly_saving": round(action_monthly_saving, 2),
            "action_annual_saving": round(action_annual_saving, 2),
            "net_daily_outcome": round(net_daily_outcome, 2),
            "net_annual_outcome": round(net_annual_outcome, 2),
            "total_daily_profit": total_daily_profit,
            "total_annual_profit": total_annual_profit,
            "total_saved_kwh": total_saved_kwh,
            "total_daily_loss": total_daily_loss,
            "total_annual_loss": total_annual_loss,
            "daily_consumption_cost": daily_consumption_cost,
            "annual_consumption_cost": annual_consumption_cost,
            "daily_waste_loss": daily_waste_loss,
            "annual_waste_loss": annual_waste_loss,
            "energy_reduction_pct": round(action_pct, 1),
            "baseline_water": round(baseline_water, 1),
            "simulated_water": round(simulated_water, 1),
            "water_saved": round(water_saved, 1),
            "water_reduction_pct": round(water_pct, 1),
            "cost_saved_daily": round(cost_saved_daily, 2),
            "monthly_saving": round(monthly_saving, 2),
            "annual_saving": round(annual_saving, 2),
            "net_cost_saved_daily": round(net_cost_saved_daily, 2),
            "net_annual_saving": round(net_annual_saving, 2),
            "co2_reduction_monthly_kg": round(monthly_co2_kg, 1),
            "co2_reduction_annual_tons": round(annual_co2_tons, 2),
            "sustainability_impact_points": sustainability_impact,
            "is_net_loss": is_net_loss,
            "status_text": status_text,
            "net_financial_loss_daily": round(net_financial_loss_daily, 2),
            "net_financial_loss_monthly": round(net_financial_loss_monthly, 2),
            "net_financial_loss_annual": round(net_financial_loss_annual, 2),
            "net_energy_waste_daily": round(net_energy_waste_daily, 1),
            "thermal_penalty": {
                "ambient_temperature": temp_val,
                "reference_temperature": ref_temp,
                "delta_temp": round(delta_temp, 1),
                "is_cool_bonus": is_cool_bonus,
                "heat_penalty_pct": heat_penalty_pct,
                "thermal_loss_kwh": thermal_loss_kwh,
                "thermal_loss_cost_daily": thermal_loss_cost_daily,
                "thermal_loss_cost_monthly": thermal_loss_cost_monthly,
                "thermal_loss_cost_annual": thermal_loss_cost_annual,
                "cool_bonus_pct": cool_bonus_pct,
                "thermal_saving_kwh": thermal_saving_kwh,
                "thermal_saving_cost_daily": thermal_saving_cost_daily,
                "thermal_saving_cost_monthly": thermal_saving_cost_monthly,
                "thermal_saving_cost_annual": thermal_saving_cost_annual,
                "cop_degradation_pct": cop_degradation_pct,
                "cop_boost_pct": cop_boost_pct,
                "cop_net_pct": cop_boost_pct if is_cool_bonus else -cop_degradation_pct,
                "severity": (
                    "CRITICAL HEATWAVE PENALTY" if delta_temp >= 10.0 else (
                        "HIGH THERMAL STRESS" if delta_temp >= 5.0 else (
                            "MODERATE HEAT LOAD" if delta_temp > 0.0 else (
                                "HIGH NATURAL COOLING BENEFIT" if delta_temp <= -10.0 else (
                                    "SUBSTANTIAL WEATHER COOLING BONUS" if delta_temp <= -5.0 else (
                                        "FAVORABLE COOL AMBIENT PROFIT" if delta_temp < 0.0 else "OPTIMAL 25°C DESIGN COMFORT"
                                    )
                                )
                            )
                        )
                    )
                )
            },
            "hourly_labels": labels,
            "hourly_before": hourly_before,
            "hourly_after": hourly_after
        }

    @classmethod
    def compare_scenarios(cls, building_data, scenarios_list, temperature=30.0):
        """
        Evaluates multiple scenario proposals factoring in ambient temperature.
        """
        results = []
        for idx, sc in enumerate(scenarios_list):
            action = sc.get("action", "reduce_ac_1h")
            dur = sc.get("duration", 1.0)
            name = sc.get("name", f"Scenario {chr(65 + idx)}")
            sim = cls.simulate_action(building_data, action, duration_hours=dur, temperature=temperature)
            sim["scenario_name"] = name
            results.append(sim)

        # Rank by annual financial outcome (or least loss) and sustainability impact
        sorted_scenarios = sorted(
            results,
            key=lambda x: (x["annual_saving"] * 0.7 + x["sustainability_impact_points"] * 50000.0),
            reverse=True
        )
        best_scenario = sorted_scenarios[0] if sorted_scenarios else None

        if best_scenario:
            ann_sav = best_scenario["annual_saving"]
            sav_str = f"₹{ann_sav:,.0f}" if ann_sav >= 0 else f"-₹{abs(ann_sav):,.0f} DEFICIT"
            summary = (
                f"{best_scenario['scenario_name']} ({best_scenario['action_name']}) delivers highest overall performance: "
                f"{sav_str}/year, {best_scenario['energy_saved']} kWh/day net saved, "
                f"and {best_scenario['sustainability_impact_points']:+.1f} points to Campus Sustainability Index."
            )
        else:
            summary = "No scenarios compared."

        return {
            "scenarios": results,
            "best_scenario": best_scenario,
            "recommendation_summary": summary
        }
