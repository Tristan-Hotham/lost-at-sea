// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8841; set PORT to change).
const { chromium } = require("playwright");
// Leaflet from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here.
const LEAF = process.env.LEAFLET_DIST || "/dev/shm/lost/npm/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8841) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    await p.click("#focusRow .btn:nth-child(3)"); await p.waitForTimeout(1200); await shot("#atlas", "bermuda");
    await p.click('#unitRow [data-u="cell"]'); await p.waitForTimeout(900); await shot("#atlas", "bermuda_cells");
    await p.click('#unitRow [data-u="area"]'); await p.click('#measRow [data-m="L"]'); await p.click("#focusRow .btn:nth-child(2)"); await p.waitForTimeout(1000); await shot("#atlas", "world_losses");
    await p.click('#measRow [data-m="M"]'); await p.waitForTimeout(700); await shot("#atlas", "world_modern");
    await p.click('#measRow [data-m="T"]'); await p.click('#colRow [data-c="conf"]'); await p.click("#focusRow .btn:nth-child(6)"); await p.waitForTimeout(1000); await shot("#atlas", "bass_conf");
    await p.click('#colRow [data-c="kind"]');
    await p.fill("#q", "Flight 19"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await shot("#atlas", "search_flight19");
    await p.fill("#q", "Mediterr"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await shot("#atlas", "search_med");
    await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(1000); await shot("#atlas", "dragon");
    await p.click("#focusRow .btn:nth-child(5)"); await p.waitForTimeout(1000); await shot("#atlas", "michigan");
    await p.click("#focusRow .btn:nth-child(2)"); await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.click('.lyrPanel [data-k="losses"]'); await p.waitForTimeout(1500); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    await p.click('.lyrBtn'); await p.click('.lyrPanel .reset'); await p.click('.lyrBtn');
    for (const c of ["decChart", "forest", "famTable", "funnel", "worseTable", "cellTable"]) await shot("#" + c, c);
    await p.click('#forRow [data-f="M"]'); await p.waitForTimeout(400); await shot("#forest", "forest_modern");
    await p.click('#forRow [data-f="T_lanes"]'); await p.waitForTimeout(400); await shot("#forest", "forest_lanes");
    await p.click('#funRow [data-u="cell"]'); await p.waitForTimeout(400); await shot("#funnel", "funnel_cells");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#forest", "dark_forest");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
