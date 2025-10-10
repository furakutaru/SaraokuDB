(() => {
var exports = {};
exports.id = 136;
exports.ids = [136];
exports.modules = {

/***/ 75193:
/***/ ((module) => {

"use strict";
module.exports = require("@emotion/react/jsx-runtime");

/***/ }),

/***/ 18038:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/react");

/***/ }),

/***/ 98704:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/react-dom/server-rendering-stub");

/***/ }),

/***/ 97897:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/react-server-dom-webpack/client");

/***/ }),

/***/ 56786:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/compiled/react/jsx-runtime");

/***/ }),

/***/ 5868:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/app-render/app-render");

/***/ }),

/***/ 41844:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/app-render/get-segment-param");

/***/ }),

/***/ 96624:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/future/helpers/interception-routes");

/***/ }),

/***/ 75281:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/server/future/route-modules/route-module");

/***/ }),

/***/ 57085:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/app-router-context");

/***/ }),

/***/ 20199:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/hash");

/***/ }),

/***/ 39569:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/hooks-client-context");

/***/ }),

/***/ 30893:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/add-path-prefix");

/***/ }),

/***/ 17887:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/handle-smooth-scroll");

/***/ }),

/***/ 98735:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/is-bot");

/***/ }),

/***/ 68231:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/parse-path");

/***/ }),

/***/ 54614:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/path-has-prefix");

/***/ }),

/***/ 53750:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/router/utils/remove-trailing-slash");

/***/ }),

/***/ 79618:
/***/ ((module) => {

"use strict";
module.exports = require("next/dist/shared/lib/server-inserted-html");

/***/ }),

/***/ 71017:
/***/ ((module) => {

"use strict";
module.exports = require("path");

/***/ }),

/***/ 57310:
/***/ ((module) => {

"use strict";
module.exports = require("url");

/***/ }),

/***/ 52058:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GlobalError: () => (/* reexport default from dynamic */ next_dist_client_components_error_boundary__WEBPACK_IMPORTED_MODULE_2___default.a),
/* harmony export */   __next_app__: () => (/* binding */ __next_app__),
/* harmony export */   originalPathname: () => (/* binding */ originalPathname),
/* harmony export */   pages: () => (/* binding */ pages),
/* harmony export */   routeModule: () => (/* binding */ routeModule),
/* harmony export */   tree: () => (/* binding */ tree)
/* harmony export */ });
/* harmony import */ var next_dist_server_future_route_modules_app_page_module__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(7262);
/* harmony import */ var next_dist_server_future_route_modules_app_page_module__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_future_route_modules_app_page_module__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var next_dist_server_future_route_kind__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(19513);
/* harmony import */ var next_dist_client_components_error_boundary__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(31823);
/* harmony import */ var next_dist_client_components_error_boundary__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(next_dist_client_components_error_boundary__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var next_dist_server_app_render_entry_base__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(12502);
/* harmony import */ var next_dist_server_app_render_entry_base__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_app_render_entry_base__WEBPACK_IMPORTED_MODULE_3__);
/* harmony reexport (unknown) */ var __WEBPACK_REEXPORT_OBJECT__ = {};
/* harmony reexport (unknown) */ for(const __WEBPACK_IMPORT_KEY__ in next_dist_server_app_render_entry_base__WEBPACK_IMPORTED_MODULE_3__) if(["default","tree","pages","GlobalError","originalPathname","__next_app__","routeModule"].indexOf(__WEBPACK_IMPORT_KEY__) < 0) __WEBPACK_REEXPORT_OBJECT__[__WEBPACK_IMPORT_KEY__] = () => next_dist_server_app_render_entry_base__WEBPACK_IMPORTED_MODULE_3__[__WEBPACK_IMPORT_KEY__]
/* harmony reexport (unknown) */ __webpack_require__.d(__webpack_exports__, __WEBPACK_REEXPORT_OBJECT__);
// @ts-ignore this need to be imported from next/dist to be external


const AppPageRouteModule = next_dist_server_future_route_modules_app_page_module__WEBPACK_IMPORTED_MODULE_0__.AppPageRouteModule;
// We inject the tree and pages here so that we can use them in the route
// module.
const tree = {
        children: [
        '',
        {
        children: [
        'simple-horse',
        {
        children: [
        '[id]',
        {
        children: ['__PAGE__', {}, {
          page: [() => Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 99265)), "/Users/yum.ishii/SaraokuDB/frontend/app/simple-horse/[id]/page.tsx"],
          
        }]
      },
        {
        
        
      }
      ]
      },
        {
        
        metadata: {
    icon: [(async (props) => (await Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 57481))).default(props))],
    apple: [],
    openGraph: [],
    twitter: [],
    manifest: undefined
  }
      }
      ]
      },
        {
        'layout': [() => Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 51921)), "/Users/yum.ishii/SaraokuDB/frontend/app/layout.tsx"],
'loading': [() => Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 96330)), "/Users/yum.ishii/SaraokuDB/frontend/app/loading.tsx"],
'not-found': [() => Promise.resolve(/* import() eager */).then(__webpack_require__.t.bind(__webpack_require__, 95493, 23)), "next/dist/client/components/not-found-error"],
        metadata: {
    icon: [(async (props) => (await Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 57481))).default(props))],
    apple: [],
    openGraph: [],
    twitter: [],
    manifest: undefined
  }
      }
      ]
      }.children;
const pages = ["/Users/yum.ishii/SaraokuDB/frontend/app/simple-horse/[id]/page.tsx"];

// @ts-expect-error - replaced by webpack/turbopack loader

const __next_app_require__ = __webpack_require__
const __next_app_load_chunk__ = () => Promise.resolve()
const originalPathname = "/simple-horse/[id]/page";
const __next_app__ = {
    require: __next_app_require__,
    loadChunk: __next_app_load_chunk__
};

// Create and export the route module that will be consumed.
const routeModule = new AppPageRouteModule({
    definition: {
        kind: next_dist_server_future_route_kind__WEBPACK_IMPORTED_MODULE_1__.RouteKind.APP_PAGE,
        page: "/simple-horse/[id]/page",
        pathname: "/simple-horse/[id]",
        // The following aren't used in production.
        bundlePath: "",
        filename: "",
        appPaths: []
    },
    userland: {
        loaderTree: tree
    }
});

//# sourceMappingURL=app-page.js.map

/***/ }),

/***/ 13066:
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 88010))

/***/ }),

/***/ 88010:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ SimpleHorsePage)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(57114);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(next_navigation__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(17421);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_mui_material__WEBPACK_IMPORTED_MODULE_3__);
/* __next_internal_client_entry_do_not_use__ default auto */ 



function SimpleHorsePage() {
    const params = (0,next_navigation__WEBPACK_IMPORTED_MODULE_1__.useParams)();
    const router = (0,next_navigation__WEBPACK_IMPORTED_MODULE_1__.useRouter)();
    const [horse, setHorse] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null);
    const [loading, setLoading] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true);
    const [error, setError] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null);
    (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(()=>{
        const fetchHorseData = async ()=>{
            try {
                const horseId = Number(params.id);
                if (!horseId || isNaN(horseId)) {
                    throw new Error("無効な馬IDです");
                }
                console.log("馬データを取得中...");
                // 相対パスで直接JSONファイルを取得
                const response = await fetch("/data/horses_combined.json", {
                    cache: "no-store",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error("データの取得に失敗しました:", {
                        status: response.status,
                        statusText: response.statusText,
                        error: errorText
                    });
                    throw new Error(`データの取得に失敗しました (${response.status})`);
                }
                const data = await response.json();
                console.log("データを取得しました", {
                    dataKeys: Object.keys(data),
                    hasHorses: Array.isArray(data.horses),
                    horsesCount: data.horses?.length,
                    firstHorseId: data.horses?.[0]?.id,
                    firstHorseName: data.horses?.[0]?.name
                });
                // デバッグ用に全ての馬のIDをログ出力
                console.log("利用可能な馬のID（先頭10件）:", data.horses.slice(0, 10).map((h)=>h.id).join(", "));
                // 文字列のIDを数値に変換して比較
                const horseData = data.horses?.find((h)=>{
                    const id = typeof h.id === "string" ? parseInt(h.id, 10) : h.id;
                    return id === horseId;
                });
                if (!horseData) {
                    console.error("馬データが見つかりませんでした。検索したID:", horseId);
                    console.error("利用可能な馬の数:", data.horses?.length);
                    console.error("先頭の馬のIDと名前:", data.horses[0]?.id, data.horses[0]?.name);
                    throw new Error(`ID: ${horseId} の馬データが見つかりませんでした`);
                }
                console.log("マッチした馬データ:", horseData);
                setHorse({
                    id: horseData.id,
                    name: horseData.name,
                    sex: horseData.sex,
                    age: horseData.age,
                    weight: horseData.weight,
                    comment: horseData.comment,
                    seller: horseData.seller
                });
            } catch (err) {
                console.error("エラーが発生しました:", err);
                setError(err instanceof Error ? err.message : "不明なエラーが発生しました");
            } finally{
                setLoading(false);
            }
        };
        fetchHorseData();
    }, [
        params.id
    ]);
    if (loading) {
        return /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
            sx: {
                p: 3,
                textAlign: "center"
            },
            children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                children: "読み込み中..."
            })
        });
    }
    if (error) {
        return /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
            sx: {
                p: 3,
                textAlign: "center"
            },
            children: [
                /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                    color: "error",
                    children: [
                        "エラー: ",
                        error
                    ]
                }),
                /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Button, {
                    variant: "contained",
                    onClick: ()=>window.location.reload(),
                    sx: {
                        mt: 2
                    },
                    children: "再読み込み"
                })
            ]
        });
    }
    if (!horse) {
        return /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
            sx: {
                p: 3,
                textAlign: "center"
            },
            children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                children: "馬のデータが見つかりませんでした"
            })
        });
    }
    return /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
        sx: {
            p: 3,
            maxWidth: 800,
            margin: "0 auto"
        },
        children: [
            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Button, {
                variant: "outlined",
                onClick: ()=>router.push(`/horses/${horse.id}`),
                sx: {
                    mb: 2
                },
                children: "← 元のページに戻る"
            }),
            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Card, {
                sx: {
                    mb: 3
                },
                children: /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.CardContent, {
                    children: [
                        /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                            variant: "h5",
                            component: "div",
                            gutterBottom: true,
                            children: horse.name
                        }),
                        /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                            color: "text.secondary",
                            gutterBottom: true,
                            children: [
                                horse.sex,
                                " | ",
                                horse.age,
                                "歳"
                            ]
                        }),
                        horse.weight && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                            variant: "body1",
                            sx: {
                                mt: 2
                            },
                            children: [
                                /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("strong", {
                                    children: "体重:"
                                }),
                                " ",
                                horse.weight,
                                " kg"
                            ]
                        }),
                        horse.seller && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                            variant: "body1",
                            sx: {
                                mt: 1
                            },
                            children: [
                                /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("strong", {
                                    children: "販売者:"
                                }),
                                " ",
                                horse.seller
                            ]
                        }),
                        horse.comment && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                            sx: {
                                mt: 3,
                                p: 2,
                                backgroundColor: "#f5f5f5",
                                borderRadius: 1
                            },
                            children: [
                                /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                    variant: "subtitle1",
                                    gutterBottom: true,
                                    children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("strong", {
                                        children: "コメント:"
                                    })
                                }),
                                /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                    variant: "body2",
                                    whiteSpace: "pre-line",
                                    children: horse.comment
                                })
                            ]
                        })
                    ]
                })
            })
        ]
    });
}


/***/ }),

/***/ 99265:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   $$typeof: () => (/* binding */ $$typeof),
/* harmony export */   __esModule: () => (/* binding */ __esModule),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var next_dist_build_webpack_loaders_next_flight_loader_module_proxy__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(61363);

const proxy = (0,next_dist_build_webpack_loaders_next_flight_loader_module_proxy__WEBPACK_IMPORTED_MODULE_0__.createProxy)(String.raw`/Users/yum.ishii/SaraokuDB/frontend/app/simple-horse/[id]/page.tsx`)

// Accessing the __esModule property and exporting $$typeof are required here.
// The __esModule getter forces the proxy target to create the default export
// and the $$typeof value is for rendering logic to determine if the module
// is a client boundary.
const { __esModule, $$typeof } = proxy;
const __default__ = proxy.default;


/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (__default__);

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, [587,668,717,610], () => (__webpack_exec__(52058)));
module.exports = __webpack_exports__;

})();