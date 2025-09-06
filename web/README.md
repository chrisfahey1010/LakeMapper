# LakeMapper Web

React + Vite web UI to browse lakes, view merged polygons and depth contours, and see fish species.

## Prereqs

- Node 18+
- Run the Python pipeline to populate `output/`

## Dev

```bash
cd web
npm install
npm run sync:data     # copies ../output → web/public/output
npm run dev
```

Open http://localhost:5173

## Build

```bash
npm run build
npm run preview
```

For AWS Amplify, set build command to `npm ci && npm run build` and publish the `web/dist` folder. Ensure the `output/` artifacts are uploaded alongside or served from a CDN bucket at `/output/...` paths.


