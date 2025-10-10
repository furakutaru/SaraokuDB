"use strict";
(() => {
var exports = {};
exports.id = 986;
exports.ids = [986];
exports.modules = {

/***/ 22037:
/***/ ((module) => {

module.exports = require("os");

/***/ }),

/***/ 88648:
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

// NAMESPACE OBJECT: ./app/api/horses/route.ts
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
;// CONCATENATED MODULE: ./app/api/horses/route.ts

// バックエンドのベースURL
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
// バックエンドのAPIを呼び出す関数
async function fetchFromBackend(url) {
    console.log(`Fetching from backend: ${BACKEND_URL}${url}`);
    const response = await fetch(`${BACKEND_URL}${url}`, {
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    });
    if (!response.ok) {
        const errorData = await response.json().catch(()=>({}));
        console.error("Backend API error:", {
            status: response.status,
            statusText: response.statusText,
            errorData
        });
        throw new Error(errorData.detail?.error || `Failed to fetch data from backend: ${response.status} ${response.statusText}`);
    }
    return response.json();
}
async function GET(request) {
    try {
        const { searchParams } = new URL(request.url);
        const queryString = searchParams.toString();
        const apiUrl = queryString ? `/api/horses?${queryString}` : "/api/horses";
        console.log("Fetching horses from backend...", {
            apiUrl
        });
        // バックエンドから馬の一覧を取得
        const data = await fetchFromBackend(apiUrl);
        console.log("Received data from backend:", {
            hasHorses: !!data.horses,
            horsesCount: data.horses?.length || 0,
            metadata: data.metadata
        });
        // バックエンドからのレスポンスをそのまま返す
        return next_response/* default */.Z.json(data);
    } catch (error) {
        console.error("Error in GET /api/horses:", error);
        return next_response/* default */.Z.json({
            error: "Failed to fetch horses",
            details: error instanceof Error ? error.message : "Unknown error"
        }, {
            status: 500
        });
    }
}
const dynamic = "force-dynamic";

;// CONCATENATED MODULE: ./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?page=%2Fapi%2Fhorses%2Froute&name=app%2Fapi%2Fhorses%2Froute&pagePath=private-next-app-dir%2Fapi%2Fhorses%2Froute.ts&appDir=%2FUsers%2Fyum.ishii%2FSaraokuDB%2Ffrontend%2Fapp&appPaths=%2Fapi%2Fhorses%2Froute&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&basePath=&assetPrefix=&nextConfigOutput=&preferredRegion=&middlewareConfig=e30%3D!

// @ts-ignore this need to be imported from next/dist to be external


// @ts-expect-error - replaced by webpack/turbopack loader

const AppRouteRouteModule = app_route_module.AppRouteRouteModule;
// We inject the nextConfigOutput here so that we can use them in the route
// module.
const nextConfigOutput = ""
const routeModule = new AppRouteRouteModule({
    definition: {
        kind: route_kind.RouteKind.APP_ROUTE,
        page: "/api/horses/route",
        pathname: "/api/horses",
        filename: "route",
        bundlePath: "app/api/horses/route"
    },
    resolvedPagePath: "/Users/yum.ishii/SaraokuDB/frontend/app/api/horses/route.ts",
    nextConfigOutput,
    userland: route_namespaceObject
});
// Pull out the exports that we need to expose from the module. This should
// be eliminated when we've moved the other routes to the new format. These
// are used to hook into the route.
const { requestAsyncStorage , staticGenerationAsyncStorage , serverHooks , headerHooks , staticGenerationBailout  } = routeModule;
const originalPathname = "/api/horses/route";


//# sourceMappingURL=app-route.js.map

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, [587,501,335], () => (__webpack_exec__(88648)));
module.exports = __webpack_exports__;

})();