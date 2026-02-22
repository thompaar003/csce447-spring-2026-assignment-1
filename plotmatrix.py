import pandas as pd
import json

def generate_temperature_matrix(file_path='temperature_daily.csv', start_year=2008, end_year=2017):
    """
    Generates an interactive D3.js matrix visualization for daily temperatures.
    """
    # Load data
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])

    # Filter years
    df = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]

    data_dict = []
    grouped = df.groupby([df['date'].dt.year, df['date'].dt.month])
    for (year, month), group in grouped:
        max_temp = group['max_temperature'].max()
        min_temp = group['min_temperature'].min()
        days = [{"date": row['date'].strftime("%Y-%m-%d"), 
                 "max_temperature": row['max_temperature'], 
                 "min_temperature": row['min_temperature']} for _, row in group.iterrows()]
        data_dict.append({
            "year": int(year),
            "month": int(month),
            "max_temperature": float(max_temp),
            "min_temperature": float(min_temp),
            "days": days
        })

    json_data = json.dumps(data_dict)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Temperature Matrix View</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        /* Matrix cell borders */
        .cell {{
            stroke: #fff;
            stroke-width: 1px;
            cursor: pointer;
        }}
        /* Axis line and tick styles */
        .axis line, .axis path {{
            stroke: #000;
            stroke-width: 1px;
        }}
        .axis text {{
            fill: #000;
        }}
        /* Tooltip styling */
        .tooltip {{
            position: absolute;
            text-align: left;
            padding: 8px;
            font: 12px sans-serif;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
            z-index: 10;
        }}
        /* MAX temperature daily line color */
        .line-max {{
            fill: none;
            stroke: #64A33D;
            stroke-width: 1.5px;
            opacity: 1.0;
        }}
        /* MIN temperature daily line color */
        .line-min {{
            fill: none;
            stroke: #7C3DA3;
            stroke-width: 1.5px;
            opacity: 1.0;
        }}
        .interactive-rect {{
            fill: transparent;
            cursor: pointer;
        }}
        .legend text {{
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h2>Hong Kong Monthly Temperature ({start_year}-{end_year})</h2>
    <p>Click on the matrix to toggle between <b>Max Temperature</b> and <b>Min Temperature</b> background coloring.</p>
    <div id="chart"></div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const rawData = {json_data};
        
        // CHART DIMENSIONS: Modify margin, width, or height to change the overall size
        const margin = {{top: 50, right: 100, bottom: 50, left: 80}},
              width = 1000 - margin.left - margin.right,
              height = 800 - margin.top - margin.bottom;

        const years = Array.from(new Set(rawData.map(d => d.year))).sort();
        const months = d3.range(1, 13);
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

        const svg = d3.select("#chart")
            .append("svg")
            .attr("width", width + margin.left + margin.right + 100) // extra space for legend
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        const gridWidth = width / years.length;
        const gridHeight = height / months.length;

        // SCALES AND SPACING: Modify paddingInner (0 to 1) to change the gap between cells
        const x = d3.scaleBand()
            .domain(years)
            .range([0, width])
            .paddingInner(0.15)
            .paddingOuter(0.2);

        const y = d3.scaleBand()
            .domain(months)
            .range([0, height])
            .paddingInner(0.15)
            .paddingOuter(0.2);

        svg.append("g")
            .attr("class", "axis")
            .call(d3.axisTop(x).tickSize(5))
            .selectAll("text")
            .style("font-size", "14px");

        // Explicit horizontal line for years axis
        svg.append("line")
            .attr("x1", 0)
            .attr("x2", width)
            .attr("y1", 0)
            .attr("y2", 0)
            .attr("stroke", "#000")
            .attr("stroke-width", "1px");

        svg.append("g")
            .attr("class", "axis")
            .call(d3.axisLeft(y).tickFormat(d => monthNames[d-1]).tickSize(5))
            .selectAll("text")
            .style("font-size", "14px");

        // Explicit vertical line for months axis
        svg.append("line")
            .attr("x1", 0)
            .attr("x2", 0)
            .attr("y1", 0)
            .attr("y2", height)
            .attr("stroke", "#000")
            .attr("stroke-width", "1px");

        // COLOR SCALE: Change the domain or range (d3.scheme) to use different colors for the background
        const colorScale = d3.scaleQuantize()
            .domain([0, 40])
            .range(d3.schemeRdYlBu[11].reverse());

        let currentMode = "max";

        const cells = svg.selectAll(".cellGroup")
            .data(rawData)
            .enter().append("g")
            .attr("class", "cellGroup")
            .attr("transform", d => `translate(${{x(d.year)}},${{y(d.month)}})`);

        cells.append("rect")
            .attr("class", "cell")
            .attr("width", x.bandwidth())
            .attr("height", y.bandwidth())
            .style("fill", d => colorScale(d.max_temperature));

        // INTERNAL CELL PADDING: Gap between the line graphs and the edges of their cell
        const chartPadding = 4;
        const xLine = d3.scaleLinear().domain([1, 31]).range([chartPadding, x.bandwidth() - chartPadding]);
        const yLine = d3.scaleLinear().domain([0, 40]).range([y.bandwidth() - chartPadding, chartPadding]);

        const lineMax = d3.line()
            .x(d => xLine(parseInt(d.date.split("-")[2])))
            .y(d => yLine(d.max_temperature));

        const lineMin = d3.line()
            .x(d => xLine(parseInt(d.date.split("-")[2])))
            .y(d => yLine(d.min_temperature));

        cells.append("path")
            .attr("class", "line-max")
            .attr("d", d => lineMax(d.days))
            .style("pointer-events", "none");

        cells.append("path")
            .attr("class", "line-min")
            .attr("d", d => lineMin(d.days))
            .style("pointer-events", "none");

        const tooltip = d3.select("#tooltip");

        cells.append("rect")
            .attr("class", "interactive-rect")
            .attr("width", x.bandwidth())
            .attr("height", y.bandwidth())
            .on("mousemove", function(event, d) {{
                const [mouseX, mouseY] = d3.pointer(event);
                const day = Math.round(xLine.invert(mouseX));
                const dayData = d.days.find(dayObj => parseInt(dayObj.date.split("-")[2]) === day);
                
                if (dayData) {{
                    tooltip.transition()
                        .duration(100)
                        .style("opacity", .9);
                    tooltip.html(`<b>${{dayData.date}}</b><br/>Max Temp: ${{dayData.max_temperature}}°C<br/>Min Temp: ${{dayData.min_temperature}}°C`)
                        .style("left", (event.pageX + 15) + "px")
                        .style("top", (event.pageY - 28) + "px");
                    
                    // Add vertical line inside the cell locally
                    d3.select(this.parentNode).selectAll(".hover-line").remove();
                    d3.select(this.parentNode).append("line")
                        .attr("class", "hover-line")
                        .attr("x1", xLine(day)).attr("x2", xLine(day))
                        .attr("y1", 0).attr("y2", y.bandwidth())
                        .style("stroke", "#000")
                        .style("stroke-width", "1px")
                        .style("stroke-dasharray", "2,2")
                        .style("pointer-events", "none");
                }}
            }})
            .on("mouseout", function(d) {{
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
                d3.selectAll(".hover-line").remove();
            }})
            .on("click", function() {{
                 currentMode = currentMode === "max" ? "min" : "max";
                 svg.selectAll(".cell")
                    .transition().duration(500)
                    .style("fill", d => currentMode === "max" ? colorScale(d.max_temperature) : colorScale(d.min_temperature));
            }});

        // Legend
        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${{width + 20}}, 50)`);

        const legendColors = colorScale.range().slice().reverse();
        const legendScale = d3.scaleLinear().domain([40, 0]).range([0, 300]);
        const legendAxis = d3.axisRight(legendScale)
            .tickValues(d3.range(0, 41, 4))
            .tickFormat(d => d + "°C");

        legend.selectAll("rect")
            .data(legendColors)
            .enter().append("rect")
            .attr("y", (d, i) => i * (300 / 11))
            .attr("width", 20)
            .attr("height", 300 / 11)
            .style("fill", d => d)
            .style("stroke", "#ccc")
            .style("stroke-width", "0.5px");

        legend.append("g")
            .attr("transform", "translate(20, 0)")
            .call(legendAxis);

    </script>
</body>
</html>
"""

    with open('index.html', 'w') as f:
        f.write(html_content)

    print(f"Successfully generated matrix for {start_year}-{end_year} in index.html")

if __name__ == "__main__":
    # Example usage:
    generate_temperature_matrix('temperature_daily.csv', start_year=2008, end_year=2017)