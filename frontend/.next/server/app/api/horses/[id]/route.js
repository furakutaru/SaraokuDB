"use strict";
(() => {
var exports = {};
exports.id = 750;
exports.ids = [750];
exports.modules = {

/***/ 22037:
/***/ ((module) => {

module.exports = require("os");

/***/ }),

/***/ 62542:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  headerHooks: () => (/* binding */ headerHooks),
  originalPathname: () => (/* binding */ originalPathname),
  requestAsyncStorage: () => (/* binding */ requestAsyncStorage),
  routeModule: () => (/* binding */ routeModule),
  serverHooks: () => (/* binding */ serverHooks),
  staticGenerationAsyncStorage: () => (/* binding */ staticGenerationAsyncStorage),
  staticGenerationBailout: () => (/* binding */ staticGenerationBailout)
});

// NAMESPACE OBJECT: ./app/api/horses/[id]/route.ts
var route_namespaceObject = {};
__webpack_require__.r(route_namespaceObject);
__webpack_require__.d(route_namespaceObject, {
  GET: () => (GET),
  dynamic: () => (dynamic)
});

// EXTERNAL MODULE: ./node_modules/next/dist/server/node-polyfill-headers.js
var node_polyfill_headers = __webpack_require__(42394);
// EXTERNAL MODULE: ./node_modules/next/dist/server/future/route-modules/app-route/module.js
var app_route_module = __webpack_require__(69692);
// EXTERNAL MODULE: ./node_modules/next/dist/server/future/route-kind.js
var route_kind = __webpack_require__(19513);
// EXTERNAL MODULE: ./node_modules/next/dist/server/web/exports/next-response.js
var next_response = __webpack_require__(89335);
;// CONCATENATED MODULE: ./app/api/horses/[id]/route.ts

// バックエンドのベースURL
const BACKEND_URL = "http://localhost:8001" || 0;
console.log("Backend URL:", BACKEND_URL); // デバッグ用
// バックエンドのAPIを呼び出す関数
async function fetchFromBackend(url) {
    const response = await fetch(`${BACKEND_URL}${url}`);
    if (!response.ok) {
        const error = await response.json().catch(()=>({}));
        throw new Error(error.detail?.error || "Failed to fetch data from backend");
    }
    return response.json();
}
async function GET(request, { params }) {
    try {
        // バックエンドから馬のデータを取得
        const horse = await fetchFromBackend(`/api/horses/${params.id}`);
        return next_response/* default */.Z.json(horse);
    } catch (error) {
        console.error("Error fetching horse data:", error);
        return next_response/* default */.Z.json({
            error: "Failed to fetch horse data",
            details: error instanceof Error ? error.message : String(error)
        }, {
            status: 404
        });
    }
}
const dynamic = "force-dynamic";

;// CONCATENATED MODULE: ./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?page=%2Fapi%2Fhorses%2F%5Bid%5D%2Froute&name=app%2Fapi%2Fhorses%2F%5Bid%5D%2Froute&pagePath=private-next-app-dir%2Fapi%2Fhorses%2F%5Bid%5D%2Froute.ts&appDir=%2FUsers%2Fyum.ishii%2FSaraokuDB%2Ffrontend%2Fapp&appPaths=%2Fapi%2Fhorses%2F%5Bid%5D%2Froute&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D!

// @ts-ignore this need to be imported from next/dist to be external


// @ts-expect-error - replaced by webpack/turbopack loader

const AppRouteRouteModule = app_route_module.AppRouteRouteModule;
// We inject the nextConfigOutput here so that we can use them in the route
// module.
const nextConfigOutput = ""
const routeModule = new AppRouteRouteModule({
    definition: {
        kind: route_kind.RouteKind.APP_ROUTE,
        page: "/api/horses/[id]/route",
        pathname: "/api/horses/[id]",
        filename: "route",
        bundlePath: "app/api/horses/[id]/route"
    },
    resolvedPagePath: "/Users/yum.ishii/SaraokuDB/frontend/app/api/horses/[id]/route.ts",
    nextConfigOutput,
    userland: route_namespaceObject
});
// Pull out the exports that we need to expose from the module. This should
// be eliminated when we've moved the other routes to the new format. These
// are used to hook into the route.
const { requestAsyncStorage , staticGenerationAsyncStorage , serverHooks , headerHooks , staticGenerationBailout  } = routeModule;
const originalPathname = "/api/horses/[id]/route";


//# sourceMappingURL=app-route.js.map

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, [587,501,335], () => (__webpack_exec__(62542)));
module.exports = __webpack_exports__;

})();