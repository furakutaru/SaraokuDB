"use strict";
(() => {
var exports = {};
exports.id = 711;
exports.ids = [711];
exports.modules = {

/***/ 90730:
/***/ ((module) => {

module.exports = require("next/dist/server/api-utils/node.js");

/***/ }),

/***/ 43076:
/***/ ((module) => {

module.exports = require("next/dist/server/future/route-modules/route-module.js");

/***/ }),

/***/ 59185:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  config: () => (/* binding */ config),
  "default": () => (/* binding */ next_route_loaderkind_PAGES_API_page_2Fapi_2Fcheck_data_integrity_preferredRegion_absolutePagePath_private_next_pages_2Fapi_2Fcheck_data_integrity_js_middlewareConfigBase64_e30_3D_),
  routeModule: () => (/* binding */ routeModule)
});

// NAMESPACE OBJECT: ./pages/api/check-data-integrity.js
var check_data_integrity_namespaceObject = {};
__webpack_require__.r(check_data_integrity_namespaceObject);
__webpack_require__.d(check_data_integrity_namespaceObject, {
  "default": () => (handler)
});

// EXTERNAL MODULE: ./node_modules/next/dist/server/future/route-modules/pages-api/module.js
var pages_api_module = __webpack_require__(56429);
// EXTERNAL MODULE: ./node_modules/next/dist/server/future/route-kind.js
var route_kind = __webpack_require__(47153);
// EXTERNAL MODULE: ./node_modules/next/dist/build/webpack/loaders/next-route-loader/helpers.js
var helpers = __webpack_require__(37305);
;// CONCATENATED MODULE: ./pages/api/check-data-integrity.js
// Simple mock API endpoint for data integrity check
function handler(req, res) {
    if (req.method !== "POST") {
        return res.status(405).json({
            error: "Method not allowed"
        });
    }
    try {
        const data = req.body;
        // Basic validation
        if (!Array.isArray(data)) {
            return res.status(400).json({
                error: "無効なデータ形式です: 配列が必要です"
            });
        }
        let totalIssues = 0;
        const issues = [];
        const requiredFields = [
            "id",
            "name",
            "sex",
            "age",
            "sire",
            "dam",
            "damsire"
        ];
        // Check each horse
        data.forEach((horse, index)=>{
            const horseIssues = [];
            // Check required fields
            requiredFields.forEach((field)=>{
                if (!(field in horse) || horse[field] === null || horse[field] === "") {
                    horseIssues.push({
                        field,
                        issue: "必須フィールドが不足しています",
                        value: horse[field]
                    });
                    totalIssues++;
                }
            });
            // Check auction history
            if (!horse.auction_history || !Array.isArray(horse.auction_history) || horse.auction_history.length === 0) {
                horseIssues.push({
                    field: "auction_history",
                    issue: "オークション履歴がありません",
                    value: horse.auction_history
                });
                totalIssues++;
            } else {
                // Check each auction history entry
                horse.auction_history.forEach((history, historyIndex)=>{
                    if (!history.auction_date) {
                        horseIssues.push({
                            field: `auction_history[${historyIndex}].auction_date`,
                            issue: "オークション日が設定されていません",
                            value: history.auction_date
                        });
                        totalIssues++;
                    }
                });
            }
            if (horseIssues.length > 0) {
                issues.push({
                    id: horse.id || `horse-${index}`,
                    name: horse.name || "名前不明",
                    issues: horseIssues
                });
            }
        });
        // Prepare response
        const response = {
            summary: {
                total_horses: data.length,
                horses_with_issues: issues.length,
                total_issues: totalIssues
            },
            issues: issues
        };
        return res.status(200).json(response);
    } catch (error) {
        console.error("Error in check-data-integrity:", error);
        return res.status(500).json({
            error: "データの整合性チェック中にエラーが発生しました",
            details: error.message
        });
    }
}

;// CONCATENATED MODULE: ./node_modules/next/dist/build/webpack/loaders/next-route-loader/index.js?kind=PAGES_API&page=%2Fapi%2Fcheck-data-integrity&preferredRegion=&absolutePagePath=private-next-pages%2Fapi%2Fcheck-data-integrity.js&middlewareConfigBase64=e30%3D!
// @ts-ignore this need to be imported from next/dist to be external



const PagesAPIRouteModule = pages_api_module.PagesAPIRouteModule;
// Import the userland code.
// @ts-expect-error - replaced by webpack/turbopack loader

// Re-export the handler (should be the default export).
/* harmony default export */ const next_route_loaderkind_PAGES_API_page_2Fapi_2Fcheck_data_integrity_preferredRegion_absolutePagePath_private_next_pages_2Fapi_2Fcheck_data_integrity_js_middlewareConfigBase64_e30_3D_ = ((0,helpers/* hoist */.l)(check_data_integrity_namespaceObject, "default"));
// Re-export config.
const config = (0,helpers/* hoist */.l)(check_data_integrity_namespaceObject, "config");
// Create and export the route module that will be consumed.
const routeModule = new PagesAPIRouteModule({
    definition: {
        kind: route_kind/* RouteKind */.x.PAGES_API,
        page: "/api/check-data-integrity",
        pathname: "/api/check-data-integrity",
        // The following aren't used in production.
        bundlePath: "",
        filename: ""
    },
    userland: check_data_integrity_namespaceObject
});

//# sourceMappingURL=pages-api.js.map

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../webpack-api-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, [172], () => (__webpack_exec__(59185)));
module.exports = __webpack_exports__;

})();