# vatsalmishra.org

Personal site of Vatsal Mishra. Plain static HTML, no build step.

## Layout

- `index.html`: the main page. One scrolling page in the VatsalOS skin: hero, work, writing and video, now.log, about, contact.
- `os/index.html`: the original drag-the-windows VatsalOS desktop, kept as an opt-in easter egg ("Open VatsalOS"). It is `noindex` and canonicalises to the main page.
- `assets/icons/w/`: 128px WebP copies of the pixel icons used by the main page. The PNG originals stay for `/os/`.
- `social-card.html`: source for the 1200x630 OG image. Render it at 1200x630 and save as `assets/social/vatsal-mishra-card-YYYYMMDD.jpg`, then update the `og:image` and `twitter:image` tags.

## Deploys

- Vercel (project `portfolio`) deploys `main` to production at vatsalmishra.org. Any other branch gets a protected preview URL.
- GitHub Pages also serves `main` at vatsal28.github.io.
- A push to `main` is a production deploy. Check the rendered page afterwards.

## Keeping it fresh

The numbers on the page are dated. Update them, the `now.log` entries and the footer "updated" date together:

- FakeOut: Google Play download badge (currently 10K+).
- Crabhaus: issue count from crabhaus.net/archive (shown as 100+).
- watt.cell YouTube video count (82 on 24 Oct 2026).

## Hero copy alternatives

The page currently uses option 1. To switch, replace `.lead` / `.lead-2` in the hero.

1. Recommended, in use: "I build AI products, agents and automations, most of them running on hardware in my house. By day I'm an Engineering Analyst at Google Dublin, in Trust & Safety Ads. Outside of work, I build FakeOut, write Crabhaus, and keep two home agents that help run my life."
2. Number-led: "I ship AI products from a mini PC in my living room: a fact-checking app with 10K+ downloads on Google Play, a daily AI briefing past issue 100, and agents that publish while I sleep. Day job: Engineering Analyst in Trust & Safety Ads at Google Dublin."
3. Quirky-concrete: "My house has as many AI agents as people. I'm a self-taught builder (10+ years in tech, Engineering Analyst in Trust & Safety Ads at Google by day) shipping apps, agents and automation systems on my own infra."
