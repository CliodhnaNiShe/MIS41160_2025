import xpress as xp
import csv
import gurobipy as gp
from gurobipy import GRB
import folium
import webbrowser
import os
import math





# xp.init('C:/xpressmp/bin/xpauth.xpr')

fact = 0.1025  # PV utilisation factor
# fact=0.88
SYSTEM_TYPES = {
    1: {"capacity": 50, "cost": 700, "color": "green", "label": "50kW"},
    2: {"capacity": 60, "cost": 750, "color": "cyan", "label": "60kW"},
    3: {"capacity": 70, "cost": 800, "color": "blue", "label": "70kW"},
    4: {"capacity": 100, "cost": 1000, "color": "purple", "label": "100kW"}
}

CONFIG = {
    "BUDGET": 400000,  # Increased budget
    "PENALTY_UNMET": 2000,
    "MIN_DEMAND_COVERAGE": 0.013,  # Reduced coverage
    "PRIORITY_BUILDINGS": ["SCIENCE"],  # Only one priority building
    "SOLAR_YIELD": 0.15,  # kW/m²
    "PANEL_EFFICIENCY": 0.4,
    # "PANEL_EFFICIENCY": 0.18,
    "MAX_CAPACITY": 6000,  # SRESS upper limit
    "MIN_CAPACITY": 50  # SRESS lower limit
}


# -----------------------------
# 2. Data Loading with Enhanced Validation and Error Handling
# -----------------------------

def load_data():
    """Load and preprocess all required data with comprehensive validation."""
    buildings = []
    building_data = {}

    try:
        with open('UCD_Building_Coordinates.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    building_id = row['Building_id'].strip().upper()
                    area = max(0, float(row['RoofArea']))
                    lat = float(row['X_Latitude'])
                    lon = float(row['Y_Longitude'])
                    dem = float(row['Demand'])
                    # dem = float(row['Max'])
                    # dem = float(row['Median'])
                    # dem = float(row['Noon'])

                    buildings.append(building_id)
                    building_data[building_id] = {
                        'area': area,
                        'max_capacity': min(area * CONFIG["SOLAR_YIELD"] * CONFIG["PANEL_EFFICIENCY"],
                                            CONFIG["MAX_CAPACITY"]),
                        'coords': (lat, lon),
                        'is_priority': building_id in CONFIG["PRIORITY_BUILDINGS"],
                        'demand': dem,  # Simple demand estimation
                        'name': row.get('Building_Name', building_id)
                    }
                except (ValueError, KeyError) as e:
                    print(f" Error processing building {row.get('Building_id', '?')}: {str(e)}")
                    continue

        edges = []
        edge_data = {}
        with open('MST_edges.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    node1 = row['Node1'].strip().upper()
                    node2 = row['Node2'].strip().upper()

                    if node1 not in buildings or node2 not in buildings:
                        print(f"Edge references non-existent building: {node1}-{node2}")
                        continue

                    length = max(1, float(row['Edge Length']))
                    edges.append((node1, node2))
                    edges.append((node2, node1))
                    edge_data[(node1, node2)] = {'length': length, 'cost': length * 100}  # €100 per meter
                    edge_data[(node2, node1)] = {'length': length, 'cost': length * 100}
                except (ValueError, KeyError) as e:
                    print(f" Error processing edge {row.get('Node1', '?')}-{row.get('Node2', '?')}: {str(e)}")
                    continue

        return buildings, building_data, edges, edge_data

    except FileNotFoundError as e:
        print(f" Critical error: {str(e)}")
        raise SystemExit(
            "Required data files not found. Please ensure UCD_Building_Coordinates.csv and MST_edges.csv exist.")

# -----------------------------
# 3. Optimized MILP Model with Enhanced Feasibility
# -----------------------------


def build_and_solve_model(buildings, building_data, edges, edge_data):
    """Build and solve the enhanced PV optimization model with robust constraints."""
    problem = xp.problem("UCD_Microgrid_Optimization_v4")
    system_types = list(SYSTEM_TYPES.keys())

    x = {
        (b, sys): xp.var(
            vartype=xp.binary,
            name=f"Install_{b}_{sys}"
        )
        for b in buildings
        for sys in system_types
    }

    p = {
        b: xp.var(
            lb=0,
            vartype=xp.continuous,
            name=f"Power_{b}"
        )
        for b in buildings
    }

    f = {
        e: xp.var(
            lb=0,
            vartype=xp.continuous,
            name=f"Flow_{e[0]}_{e[1]}"
        )
        for e in edges
    }

    unmet = {
        b: xp.var(
            lb=0,
            # ub=building_data[b]["demand"],
            vartype=xp.continuous,
            name=f"UnmetDemand_{b}"
        )
        for b in buildings
    }

    y = {
        b: xp.var(
            vartype=xp.binary,
            name=f"y_{b}"
        )
        for b in buildings
    }
    problem.addVariable(
        list(x.values())
        + list(p.values())
        + list(f.values())
        + list(unmet.values())
        + list(y.values())
    )

    # ========== OBJECTIVE FUNCTION ==========

    installation_cost = xp.Sum(
        x[b, sys]
        * SYSTEM_TYPES[sys]["cost"]
        * SYSTEM_TYPES[sys]["capacity"]
        for b in buildings
        for sys in system_types
    )

    penalty_cost = CONFIG["PENALTY_UNMET"] * xp.Sum(
        unmet[b] for b in buildings
    )

    problem.setObjective(
        installation_cost + penalty_cost,
        sense=xp.minimize
    )
    # ========== CONSTRAINTS ==========

    # 1. Single system per building
    problem.addConstraint([
        xp.Sum(x[b, sys] for sys in system_types) <= 1
        for b in buildings
    ])

    # 2. Link installed systems to power output
    problem.addConstraint([
        p[b] == xp.Sum(
            x[b, sys] * SYSTEM_TYPES[sys]["capacity"]
            for sys in system_types
        )
        for b in buildings
    ])

    # 3. Roof area limits
    problem.addConstraint([
        p[b] <= building_data[b]["max_capacity"]
        for b in buildings
    ])


    # 4. Budget constraint
    problem.addConstraint(
        installation_cost <= CONFIG["BUDGET"]
    )

    # 5. Power balance at each building
    for b in buildings:
        inflow = xp.Sum(
            f[e] for e in edges
            if e[1] == b
        )

        outflow = xp.Sum(
            f[e] for e in edges
            if e[0] == b
        )

        problem.addConstraint(
            fact * p[b] + inflow + unmet[b]
            == building_data[b]["demand"] + outflow
        )

    # 6. Campus-wide demand coverage
    problem.addConstraint(
        xp.Sum(fact * p[b] for b in buildings)
        >= CONFIG["MIN_DEMAND_COVERAGE"]
        * sum(building_data[b]["demand"] for b in buildings)
    )

    # 7. Link installation indicator y to x
    problem.addConstraint([
        xp.Sum(x[b, sys] for sys in system_types)
        <= len(system_types) * y[b]
        for b in buildings
    ])

    # ========== SOLVER SETUP ==========
    problem.controls.miprelstop = 0.0001  # 0.01% relative MIP gap
    problem.controls.maxtime = 600        # 10-minute limit
    problem.controls.outputlog = 1

    # ========== SOLVE ==========
    problem.optimize()

    return problem, x, p, f, unmet, building_data

# -----------------------------
# 4. Enhanced Visualization with Detailed Tooltips
# -----------------------------

def visualize_results(problem, x, p, f, buildings, building_data, edges):
    """Create interactive map with comprehensive results visualization."""
    if problem.attributes.solstatus != 1:
        print("Visualization skipped - no optimal solution found")
        return None

    value = problem.getSolution

    avg_lat = (
            sum(building_data[b]["coords"][0] for b in buildings)
            / len(buildings)
    )
    avg_lon = (
            sum(building_data[b]["coords"][1] for b in buildings)
            / len(buildings)
    )

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=16,
        tiles="cartodbpositron",
        control_scale=True
    )

    # Add buildings
    for b in buildings:
        installed_type = next(
            (
                sys for sys in SYSTEM_TYPES
                if value(x[b, sys]) > 0.5
            ),
            None
        )

        popup_content = f"""
           <div style="width: 250px">
               <h4>{building_data[b].get('name', b)}</h4>
               <table style="width:100%">
                   <tr>
                       <td><b>Demand:</b></td>
                       <td>{building_data[b]['demand']:.2f} kWh</td>
                   </tr>
                   <tr>
                       <td><b>Roof Area:</b></td>
                       <td>{building_data[b]['area']:.0f} m²</td>
                   </tr>
                   <tr>
                       <td><b>Max Capacity:</b></td>
                       <td>{building_data[b]['max_capacity']:.2f} kW</td>
                   </tr>
           """

        if installed_type is not None:
            investment = (
                    SYSTEM_TYPES[installed_type]["cost"]
                    * SYSTEM_TYPES[installed_type]["capacity"]
            )

            installed_capacity = value(p[b])

            popup_content += f"""
                <tr>
                    <td><b>System Installed:</b></td>
                    <td>{SYSTEM_TYPES[installed_type]["label"]}</td>
                </tr>
                <tr>
                    <td><b>Installed Capacity:</b></td>
                    <td>{installed_capacity:.2f} kW</td>
                </tr>
                <tr>
                    <td><b>Investment:</b></td>
                    <td>€{investment:,.0f}</td>
                </tr>
            """
        else:
            popup_content += """
                <tr>
                    <td colspan="2"><i>No PV installed</i></td>
                </tr>
            """

        popup_content += "</table></div>"

        folium.CircleMarker(
            location=building_data[b]["coords"],
            radius=6 + (3 if installed_type is not None else 0),
            color="black",
            weight=1,
            fill=True,
            fill_color=SYSTEM_TYPES.get(
                installed_type, {}
            ).get("color", "red"),
            fill_opacity=0.8,
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=building_data[b].get("name", b)
        ).add_to(m)

        folium.Marker(
            location=building_data[b]["coords"],
            icon=folium.DivIcon(
                html=(
                    "<div style='font-size:12px; margin-left:8px;'>"
                    f"{building_data[b].get('name', b)}"
                    "</div>"
                ),
                icon_size=(150, 20),
                icon_anchor=(-5, 0)
            )
        ).add_to(m)

    # Add power-flow lines
    max_flow = max(
        (value(f[e]) for e in edges),
        default=0
    )

    # Prevent division by zero if all flows are zero
    if max_flow <= 0:
        max_flow = 1

    for e in edges:
        forward_flow = value(f[e])

        if forward_flow > 0.1:
            folium.PolyLine(
                locations=[
                    building_data[e[0]]["coords"],
                    building_data[e[1]]["coords"]
                ],
                color="#4682B4",
                weight=2 + 4 * math.sqrt(forward_flow / max_flow),
                opacity=0.7,
                tooltip=(
                    f"{e[0]}→{e[1]}: "
                    f"{forward_flow:.2f} kW"
                )
            ).add_to(m)

            reverse_edge = (e[1], e[0])
            reverse_flow = (
                value(f[reverse_edge])
                if reverse_edge in f
                else 0
            )

            if forward_flow > reverse_flow:
                folium.RegularPolygonMarker(
                    location=building_data[e[1]]["coords"],
                    number_of_sides=3,
                    radius=5,
                    rotation=0,
                    color="#4682B4",
                    fill_color="#4682B4",
                    fill_opacity=0.7
                ).add_to(m)

    # Legend
    legend_html = """
       <div style="position: fixed; bottom: 50px; left: 50px;
                   width: 220px; z-index: 1000;
                   background: white; padding: 10px;
                   border: 2px solid grey; border-radius: 5px;
                   font-family: Arial; font-size: 12px;
                   box-shadow: 0 0 5px rgba(0,0,0,0.2)">
           <div style="text-align: center; font-weight: bold;
                       margin-bottom: 8px; font-size: 14px;">
               UCD PV OPTIMIZATION LEGEND
           </div>
       """

    for sys in sorted(
            SYSTEM_TYPES.values(),
            key=lambda item: item["capacity"]
    ):
        legend_html += f"""
           <div style="margin: 6px 0; display: flex;
                       align-items: center;">
               <span style="background: {sys['color']};
                            width: 16px; height: 16px;
                            display: inline-block;
                            border: 1px solid black;
                            border-radius: 50%;
                            margin-right: 8px;"></span>
                    {sys['label']} System
                    (€{sys['cost'] * sys['capacity']:,.0f})
                </div>
                """
        legend_html += """
                <div style="margin: 6px 0; display: flex;
                            align-items: center;">
                    <span style="background: red;
                                 width: 16px; height: 16px;
                                 display: inline-block;
                                 border: 1px solid black;
                                 border-radius: 50%;
                                 margin-right: 8px;"></span>
                    No PV Installed
                </div>

                <div style="margin: 6px 0; display: flex;
                            align-items: center;">
                    <span style="background: #4682B4;
                                 width: 16px; height: 3px;
                                 display: inline-block;
                                 margin-right: 8px;"></span>
                    Power Flow (thicker = more power)
                </div>
            </div>
            """

        m.get_root().html.add_child(
            folium.Element(legend_html)
        )

        output_file = "ucd_pv_optimization_v4.html"
        m.save(output_file)

        print(f"\nOptimization map saved to {output_file}")
        webbrowser.open(f"file://{os.path.abspath(output_file)}")

        return m



# -----------------------------
# 5. print installation and flows
# -----------------------------

def print_installation_and_flows(problem, x, p, f, buildings, building_data, edges,  edge_data):

    """Print clear report of PV installations and power flows."""

    if problem.attributes.solstatus != 1:
        print("No optimal solution available for reporting")
        return

    value = problem.getSolution

    print("\n" + "=" * 70)
    print(
        " PV INSTALLATION AND POWER FLOW REPORT ".center(70, "=")
    )
    print("=" * 70 + "\n")

    # 1. Buildings with PV
    installed_buildings = [
        b for b in buildings
        if any(
            value(x[b, sys]) > 0.5
            for sys in SYSTEM_TYPES
        )
    ]

    print("BUILDINGS WITH PV INSTALLATIONS:")
    print("-" * 90)

    demand_sum = 0

    if not installed_buildings:
        print("No PV systems were installed")
    else:
        print(
            f"{'Building':<25}"
            f"{'System Type':<15}"
            f"{'Capacity (kW)':<17}"
            f"{'Cost (€)':<15}"
            f"{'Demand (kWh)':<15}"
        )
        print("-" * 90)

        for b in installed_buildings:
            sys = next(
                sys for sys in SYSTEM_TYPES
                if value(x[b, sys]) > 0.5
            )

            demand_sum += building_data[b]["demand"]

            print(
                f"{building_data[b].get('name', b):<25}"
                f"{SYSTEM_TYPES[sys]['label']:<15}"
                f"{value(p[b]):<17.2f}"
                f"{SYSTEM_TYPES[sys]['cost'] * SYSTEM_TYPES[sys]['capacity']:<15}"
                f"{building_data[b]['demand']:<15.2f}"
            )

    print(
        "Total demand on buildings with PV =",
        round(demand_sum, 2)
    )

    # 2. Buildings without PV
    non_installed = [
        b for b in buildings
        if not any(
            value(x[b, sys]) > 0.5
            for sys in SYSTEM_TYPES
        )
    ]

    print("\nBUILDINGS WITHOUT PV INSTALLATIONS:")
    print("-" * 70)

    if not non_installed:
        print("All buildings have PV installations")
    else:
        print(
            f"{'Building':<25}"
            f"{'Demand (kWh)':<17}"
            f"{'Max Capacity (kW)':<20}"
        )
        print("-" * 70)

        for b in non_installed:
            print(
                f"{building_data[b].get('name', b):<25}"
                f"{building_data[b]['demand']:<17.2f}"
                f"{building_data[b]['max_capacity']:<20.2f}"
            )

    # 3. Active power flows
    active_flows = [
        (e, value(f[e]))
        for e in edges
        if value(f[e]) > 0.1
    ]

    print("\nACTIVE POWER FLOWS BETWEEN BUILDINGS:")
    print("-" * 80)

    flows = []

    if not active_flows:
        print("No significant power flows between buildings")
    else:
        print(
            f"{'From':<25}"
            f"{'To':<25}"
            f"{'Flow (kW)':<15}"
            f"{'Direction':<15}"
        )
        print("-" * 80)

        for (src, dst), forward_flow in active_flows:
            reverse_edge = (dst, src)
            reverse_flow = (
                value(f[reverse_edge])
                if reverse_edge in f
                else 0
            )

            if abs(forward_flow - reverse_flow) < 0.1:
                direction = "↔"
            elif forward_flow > reverse_flow:
                direction = "→"
            else:
                direction = "←"

            displayed_flow = max(
                forward_flow,
                reverse_flow
            )

            flows.append([
                building_data[src].get("name", src),
                building_data[dst].get("name", dst),
                round(displayed_flow, 2)
            ])

            print(
                f"{building_data[src].get('name', src):<25}"
                f"{building_data[dst].get('name', dst):<25}"
                f"{displayed_flow:<15.2f}"
                f"{direction:<15}"
            )

    flows.sort(key=lambda row: row[2], reverse=True)

    with open(
            "building_flows2.csv",
            "w",
            newline="",
            encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "From Building",
            "To Building",
            "Flow"
        ])
        writer.writerows(flows)

    print("\n" + "=" * 70)
    print(" END OF REPORT ".center(70, "="))
    print("=" * 70)



# -----------------------------
# 6. Main Execution with Comprehensive Reporting
# -----------------------------
def main():
    PV = {
        sys: 0
        for sys in SYSTEM_TYPES
    }

    print("\n" + "=" * 60)
    print(
        " UCD MICROGRID OPTIMIZATION - SRESS COMPLIANCE "
    )
    print("=" * 60 + "\n")

    # Load data
    print("Loading and validating data files...")

    try:
        buildings, building_data, edges, edge_data = load_data()

        undirected_edges = {
            tuple(sorted(e))
            for e in edges
        }

        print(
            f"Loaded {len(buildings)} buildings and "
            f"{len(undirected_edges)} connections"
        )

    except Exception as error:
        print(f"Failed to load data: {error}")
        return

    # Build and solve
    print("\nBuilding optimization model...")

    try:
        (
            problem,
            x,
            p,
            f,
            unmet,
            building_data
        ) = build_and_solve_model(
            buildings,
            building_data,
            edges,
            edge_data
        )

    except Exception as error:
        print(f"Optimization error: {error}")
        return

    solvestatus = problem.attributes.solvestatus
    solstatus = problem.attributes.solstatus

    print("Solve status:", solvestatus)
    print("Solution status:", solstatus)

    if solstatus not in [1, 2]:
        if solstatus == 2:
            print("\nModel is infeasible. Possible causes:")
            print("1. Budget too low for required installations")
            print("2. Roof areas insufficient for demand coverage")
            print("3. Minimum coverage requirement is too high")

            try:
                problem.iisfirst(1)
                problem.iiswrite(
                    0,
                    "model_iis",
                    0,
                    "l"
                )
                print(
                    "\nInfeasibility analysis written to "
                    "model_iis."
                )
            except Exception as error:
                print(
                    "Could not write the IIS analysis:",
                    error
                )
        else:
            print(
                "\nNo feasible solution was returned. Status:",
                problem.getProbStatusString()
            )

        return

    value = problem.getSolution

    installation_cost = sum(
        value(x[b, sys])
        * SYSTEM_TYPES[sys]["cost"]
        * SYSTEM_TYPES[sys]["capacity"]
        for b in buildings
        for sys in SYSTEM_TYPES
    )

    total_demand = sum(
        building_data[b]["demand"]
        for b in buildings
    )

    total_installed_pv = sum(
        value(x[b, sys])
        * SYSTEM_TYPES[sys]["capacity"]
        for b in buildings
        for sys in SYSTEM_TYPES
    )

    for sys in SYSTEM_TYPES:
        PV[sys] = sum(
            value(x[b, sys])
            for b in buildings
        )

    effective_pv_supply = fact * total_installed_pv

    print("\nPV Cost:", round(installation_cost, 2))
    print("Total budget:", CONFIG["BUDGET"])
    print("Total Demand:", round(total_demand, 2))
    print(
        "Total installed PV:",
        round(total_installed_pv, 2)
    )
    print(
        "% demand coverage by PV:",
        round(
            effective_pv_supply / total_demand * 100,
            2
        ),
        "%"
    )

    print(
        f"\n{'Building':<12}"
        f"{'Demand':<12}"
        f"{'Unmet':<12}"
        f"{'PV':<12}"
        f"{'Inflow':<15}"
        f"{'Outflow':<15}"
    )

    for b in buildings:
        inflow = sum(
            value(f[e])
            for e in edges
            if e[1] == b
        )

        outflow = sum(
            value(f[e])
            for e in edges
            if e[0] == b
        )

        print(
            f"{building_data[b].get('name', b):<12}"
            f"{building_data[b]['demand']:<12.2f}"
            f"{value(unmet[b]):<12.2f}"
            f"{value(p[b]):<12.2f}"
            f"{inflow:<15.2f}"
            f"{outflow:<15.2f}"
        )

    for sys in SYSTEM_TYPES:
        print(
            "No. of PV system type",
            SYSTEM_TYPES[sys]["capacity"],
            "kW installed =",
            round(PV[sys])
        )

    print(
        "Total installations:",
        round(sum(PV.values()))
    )

    if solstatus == 1:
        print_installation_and_flows(
            problem,
            x,
            p,
            f,
            buildings,
            building_data,
            edges,
            edge_data
        )

        print(
            "Model objective:",
            problem.attributes.objval
        )
        print(
            "Total installed PV:",
            total_installed_pv
        )
        print(
            "Installation cost:",
            installation_cost
        )
        print(
            "Total unmet demand:",
            sum(value(unmet[b]) for b in buildings)
        )

        visualize_results(
            problem,
            x,
            p,
            f,
            buildings,
            building_data,
            edges
        )

    else:
        # A feasible incumbent may exist if the time limit was reached
        print(
            "\nXpress returned a feasible but not proven-optimal "
            "solution."
        )
        print(
            "Objective:",
            problem.attributes.objval
        )


if __name__ == "__main__":
    main()




























