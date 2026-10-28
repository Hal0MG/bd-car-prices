# Getting GarirBazar's OK in writing

GarirBazar's terms say nothing about automated access, but they only grant "personal, non-commercial
transitory viewing" and forbid copying the materials or showing them publicly. A friendly yes from
someone who works there is a good start. A one-line written reply from them (a text or an email is
enough) turns it into something you can point to if anyone ever asks. Paste this into a message:

---

Hi [name],

I'm building a portfolio project on how much it really costs to import a car into Bangladesh, plus a
model that estimates what a used car should sell for. To train it I'd like to read the public car
listing pages on garirbazar.com, gently:

- **What I keep:** make, model, year, price, mileage, fuel, gearbox, location (city only) and when it was
  posted. Nothing about sellers: no names, phone numbers, emails or descriptions.
- **How:** about one page every three seconds, a few hundred pages a week at most, from one computer, and
  I identify myself in the request. I read robots.txt first and stay out of anything it disallows.
- **What I publish:** only the trained model and averages (for example "a 2015 Axio typically asks around
  X lakh"), never the listings themselves. Happy to link back to GarirBazar.
- **If you'd rather I didn't:** tell me and I stop and delete what I have.

Could you reply to confirm that's fine, or tell me who I should ask? Thank you!

[your name]

---

The collector already behaves this way, whatever the answer: `src/shotti_ml/collect/fetch.py` reads
robots.txt, waits at least two seconds between requests (three by default), stops after three failures
in a row, and the parser throws descriptions away. Raw snapshots live in `data/raw/`, which git ignores.
