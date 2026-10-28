// Builds ../intro-prado.html as one self-contained file: engine numbers and the Prado photo inlined.
// node build.js  (run from design-demos/assets)
const fs = require("fs");
const b64 = (f) => "data:image/jpeg;base64," + fs.readFileSync(f).toString("base64");
let h = fs.readFileSync("intro-src.html", "utf8");
h = h.replace("__DATA__", fs.readFileSync("prado.json", "utf8").trim()).split("__PHOTO__").join(b64("prado-plate.jpg"));
fs.writeFileSync("../intro-prado.html", h);
console.log("intro-prado.html", h.length);
