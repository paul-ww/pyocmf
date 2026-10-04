/**
 * Meter reading over time: one register, one line, readings as markers.
 * Times are shown in the record's own UTC offset, not the viewer's timezone.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

const READING_REASONS = {
  B: "Begin",
  C: "Charging",
  X: "Exception",
  E: "End",
  L: "Terminated locally",
  R: "Terminated remotely",
  A: "Aborted",
  P: "Power failure",
  S: "Suspended",
  T: "Tariff change",
};

function svg(tag, attrs = {}, text = null) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== null) node.textContent = text;
  return node;
}

function niceStep(rough) {
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const residual = rough / magnitude;
  const factor = [1, 2, 2.5, 5, 10].find((f) => residual <= f);
  return factor * magnitude;
}

function valueTicks(min, max) {
  if (min === max) {
    const pad = Math.abs(min) * 0.1 || 1;
    min -= pad;
    max += pad;
  }
  const step = niceStep((max - min) / 4);
  const start = Math.floor(min / step) * step;
  const end = Math.ceil(max / step) * step;
  const decimals = Math.max(0, -Math.floor(Math.log10(step)) + (step % 1 === 0.5 ? 1 : 0));
  const ticks = [];
  for (let v = start; v <= end + step / 2; v += step) ticks.push(Number(v.toFixed(10)));
  return { ticks, min: start, max: end, decimals };
}

function offsetMinutes(isoTime) {
  const match = /([+-])(\d{2}):(\d{2})$/.exec(isoTime);
  if (!match) return 0;
  const minutes = Number(match[2]) * 60 + Number(match[3]);
  return match[1] === "-" ? -minutes : minutes;
}

function clockTime(epochMs, offset, seconds = false) {
  const local = new Date(epochMs + offset * 60000);
  const parts = [local.getUTCHours(), local.getUTCMinutes()];
  if (seconds) parts.push(local.getUTCSeconds());
  return parts.map((n) => String(n).padStart(2, "0")).join(":");
}

function timeTicks(startMs, endMs, offset) {
  const spanMinutes = (endMs - startMs) / 60000;
  const interval = [1, 2, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440].find(
    (m) => spanMinutes / m <= 5,
  ) || 1440;
  const step = interval * 60000;
  const shift = offset * 60000;
  const ticks = [];
  for (let t = Math.ceil((startMs + shift) / step) * step - shift; t <= endMs; t += step) {
    ticks.push(t);
  }
  return ticks;
}

function averagePower(previous, point, unit) {
  const hours = (point.epochMs - previous.epochMs) / 3600000;
  if (hours <= 0) return null;
  const energy = Number(point.value) - Number(previous.value);
  if (unit === "kWh") return energy / hours;
  if (unit === "Wh") return energy / 1000 / hours;
  return null;
}

function renderChart(container, series) {
  const figure = document.createElement("div");
  figure.className = "chart";
  const tooltip = document.createElement("div");
  tooltip.className = "chart-tooltip";
  tooltip.hidden = true;
  figure.append(tooltip);
  container.append(figure);

  const points = series.points;
  const offset = offsetMinutes(points[0].time);
  const unit = series.unit || "";
  const values = points.map((p) => Number(p.value));
  const y = valueTicks(Math.min(...values), Math.max(...values));
  let active = points.length - 1;
  let svgNode = null;

  function draw() {
    const width = Math.max(figure.clientWidth, 280);
    const height = 220;
    const labelWidth = Math.max(...y.ticks.map((t) => t.toFixed(y.decimals).length)) * 7 + 14;
    const margin = { top: 14, right: 78, bottom: 28, left: labelWidth };
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const t0 = points[0].epochMs;
    const t1 = points[points.length - 1].epochMs;
    const xOf = (t) => margin.left + ((t - t0) / (t1 - t0)) * plotW;
    const yOf = (v) => margin.top + (1 - (v - y.min) / (y.max - y.min)) * plotH;

    const root = svg("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      tabindex: "0",
      "aria-label": `${series.register}: ${points[0].value} to ${points[points.length - 1].value} ${unit} between ${clockTime(t0, offset)} and ${clockTime(t1, offset)}. Use the arrow keys to step through the readings.`,
    });

    const grid = svg("g", { class: "grid" });
    const axis = svg("g", { class: "axis" });
    for (const tick of y.ticks) {
      const ty = yOf(tick);
      grid.append(svg("line", { x1: margin.left, x2: margin.left + plotW, y1: ty, y2: ty }));
      axis.append(
        svg("text", { x: margin.left - 8, y: ty + 4, "text-anchor": "end" }, tick.toFixed(y.decimals)),
      );
    }
    for (const tick of timeTicks(t0, t1, offset)) {
      axis.append(
        svg("text", { x: xOf(tick), y: height - 8, "text-anchor": "middle" }, clockTime(tick, offset)),
      );
    }
    root.append(grid, axis);

    const coords = points.map((p) => [xOf(p.epochMs), yOf(Number(p.value))]);
    const line = coords.map(([px, py], i) => `${i ? "L" : "M"}${px},${py}`).join(" ");
    const baseline = margin.top + plotH;
    root.append(
      svg("path", {
        class: "series-area",
        d: `${line} L${coords[coords.length - 1][0]},${baseline} L${coords[0][0]},${baseline} Z`,
      }),
      svg("path", { class: "series-line", d: line }),
    );

    const crosshair = svg("line", { class: "crosshair", y1: margin.top, y2: baseline });
    root.append(crosshair);

    const markers = coords.map(([px, py]) => svg("circle", { class: "marker", cx: px, cy: py, r: 4 }));
    root.append(...markers);

    const [endX, endY] = coords[coords.length - 1];
    root.append(
      svg("text", { class: "direct-label", x: endX + 10, y: endY + 4 }, `${points[points.length - 1].value} ${unit}`),
    );

    root.addEventListener("pointermove", (event) => {
      const box = root.getBoundingClientRect();
      const px = ((event.clientX - box.left) / box.width) * width;
      let nearest = 0;
      coords.forEach(([cx], i) => {
        if (Math.abs(cx - px) < Math.abs(coords[nearest][0] - px)) nearest = i;
      });
      show(nearest);
    });
    root.addEventListener("pointerleave", hide);
    root.addEventListener("blur", hide);
    root.addEventListener("focus", () => show(active));
    root.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") show(Math.min(active + 1, points.length - 1));
      else if (event.key === "ArrowLeft") show(Math.max(active - 1, 0));
      else return;
      event.preventDefault();
    });

    function show(index) {
      active = index;
      const [cx, cy] = coords[index];
      crosshair.setAttribute("x1", cx);
      crosshair.setAttribute("x2", cx);
      crosshair.style.visibility = "visible";
      markers.forEach((m, i) => m.classList.toggle("active", i === index));

      const point = points[index];
      tooltip.replaceChildren();
      const value = document.createElement("strong");
      value.textContent = `${point.value} ${unit}`;
      const when = document.createElement("div");
      when.textContent = `${clockTime(point.epochMs, offset, true)} · ${READING_REASONS[point.tx] || point.tx || "Reading"}`;
      tooltip.append(value, when);
      if (index > 0) {
        const power = averagePower(points[index - 1], point, unit);
        if (power !== null) {
          const avg = document.createElement("div");
          avg.className = "muted";
          avg.textContent = `${power.toFixed(1)} kW average since previous reading`;
          tooltip.append(avg);
        }
      }
      tooltip.hidden = false;
      const scale = figure.clientWidth / width;
      const left = cx * scale;
      const flip = left + tooltip.offsetWidth + 16 > figure.clientWidth;
      tooltip.style.left = `${flip ? left - tooltip.offsetWidth - 12 : left + 12}px`;
      tooltip.style.top = `${Math.max(0, cy * scale - tooltip.offsetHeight - 10)}px`;
    }

    function hide() {
      crosshair.style.visibility = "hidden";
      markers.forEach((m) => m.classList.remove("active"));
      tooltip.hidden = true;
    }

    hide();
    if (svgNode) svgNode.replaceWith(root);
    else figure.prepend(root);
    svgNode = root;
  }

  draw();
  let lastWidth = figure.clientWidth;
  new ResizeObserver(() => {
    if (figure.clientWidth !== lastWidth) {
      lastWidth = figure.clientWidth;
      draw();
    }
  }).observe(figure);
}
