(() => {
var exports = {};
exports.id = 331;
exports.ids = [331];
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

/***/ 1799:
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
        'test-horse',
        {
        children: ['__PAGE__', {}, {
          page: [() => Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 64181)), "/Users/yum.ishii/SaraokuDB/frontend/app/test-horse/page.tsx"],
          
        }]
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
const pages = ["/Users/yum.ishii/SaraokuDB/frontend/app/test-horse/page.tsx"];

// @ts-expect-error - replaced by webpack/turbopack loader

const __next_app_require__ = __webpack_require__
const __next_app_load_chunk__ = () => Promise.resolve()
const originalPathname = "/test-horse/page";
const __next_app__ = {
    require: __next_app_require__,
    loadChunk: __next_app_load_chunk__
};

// Create and export the route module that will be consumed.
const routeModule = new AppPageRouteModule({
    definition: {
        kind: next_dist_server_future_route_kind__WEBPACK_IMPORTED_MODULE_1__.RouteKind.APP_PAGE,
        page: "/test-horse/page",
        pathname: "/test-horse",
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

/***/ 47914:
/***/ ((__unused_webpack_module, __unused_webpack_exports, __webpack_require__) => {

Promise.resolve(/* import() eager */).then(__webpack_require__.bind(__webpack_require__, 7700))

/***/ }),

/***/ 7700:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ TestHorsePage)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(57114);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(next_navigation__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(17421);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_mui_material__WEBPACK_IMPORTED_MODULE_3__);
/* __next_internal_client_entry_do_not_use__ default auto */ 



function TestHorsePage() {
    const searchParams = (0,next_navigation__WEBPACK_IMPORTED_MODULE_1__.useSearchParams)();
    const horseId = searchParams.get("id") || "14927";
    const [horse, setHorse] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null);
    const [loading, setLoading] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true);
    const [error, setError] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(null);
    (0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(()=>{
        const fetchHorseData = async ()=>{
            try {
                console.log("馬データを取得中...");
                const response = await fetch("/data/horses_combined.json");
                if (!response.ok) {
                    throw new Error("データの取得に失敗しました");
                }
                const data = await response.json();
                console.log("データを取得しました", {
                    dataKeys: Object.keys(data),
                    hasHorses: Array.isArray(data.horses),
                    horsesCount: data.horses?.length,
                    firstHorseId: data.horses?.[0]?.id,
                    firstHorseName: data.horses?.[0]?.name
                });
                // 文字列のIDを数値に変換して比較
                const horseData = data.horses?.find((h)=>{
                    const id = typeof h.id === "string" ? parseInt(h.id, 10) : h.id;
                    return id === parseInt(horseId, 10);
                });
                if (!horseData) {
                    console.error("馬データが見つかりませんでした。検索したID:", horseId);
                    console.error("利用可能な馬の数:", data.horses?.length);
                    console.error("先頭の馬のIDと名前:", data.horses[0]?.id, data.horses[0]?.name);
                    throw new Error(`ID: ${horseId} の馬データが見つかりませんでした`);
                }
                console.log("マッチした馬データ:", horseData);
                // コメントから体重情報を抽出する関数
                const extractWeightFromComment = (comment)=>{
                    if (!comment) return null;
                    // 例: 「馬体重458kg」のようなパターンを検索
                    const weightMatch = comment.match(/馬体重(?:\s*[（(]?\s*)(\d+)(?:\s*[）)]?\s*)(?:kg|キロ|㎏)/i);
                    if (weightMatch && weightMatch[1]) {
                        return parseInt(weightMatch[1], 10);
                    }
                    return null;
                };
                // 基本情報をマージ
                const mergedData = {
                    ...horseData.basic_info,
                    ...horseData,
                    // 基本情報とトップレベルの情報をマージ（トップレベルを優先）
                    id: horseData.id,
                    name: horseData.name || horseData.basic_info?.name || "不明",
                    sex: horseData.sex || horseData.basic_info?.sex || "不明",
                    age: horseData.age || horseData.basic_info?.age || 0,
                    sire: horseData.sire || horseData.basic_info?.sire || "不明",
                    dam: horseData.dam || horseData.basic_info?.dam || "不明",
                    damsire: horseData.damsire || horseData.basic_info?.damsire || "不明",
                    // 体重情報を取得（複数のソースから順に試す）
                    weight: horseData.weight || horseData.basic_info?.weight || (horseData.comment ? extractWeightFromComment(horseData.comment) : null),
                    // レース記録をマージ
                    race_records: {
                        ...horseData.basic_info?.race_records || {},
                        ...horseData.race_records || {}
                    },
                    // その他の情報
                    sold_price: horseData.sold_price,
                    comment: horseData.comment,
                    disease_tags: horseData.disease_tags || [],
                    seller: horseData.seller || horseData.basic_info?.seller || "不明",
                    owner: horseData.owner || horseData.basic_info?.owner,
                    breeder: horseData.breeder || horseData.basic_info?.breeder,
                    trainer: horseData.trainer || horseData.basic_info?.trainer,
                    location: horseData.location || horseData.basic_info?.location,
                    auction_url: horseData.auction_url,
                    jbis_url: horseData.jbis_url,
                    image_url: horseData.image_url,
                    is_retired: horseData.is_retired,
                    retirement_date: horseData.retirement_date,
                    auction_date: horseData.auction_date,
                    is_unsold: horseData.is_unsold
                };
                setHorse(mergedData);
            } catch (err) {
                console.error("エラーが発生しました:", err);
                setError(err instanceof Error ? err.message : "不明なエラーが発生しました");
            } finally{
                setLoading(false);
            }
        };
        fetchHorseData();
    }, [
        horseId
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
    return /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
        sx: {
            p: 3,
            maxWidth: 800,
            margin: "0 auto"
        },
        children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Card, {
            sx: {
                mb: 3
            },
            children: /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.CardContent, {
                children: [
                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                        sx: {
                            display: "flex",
                            gap: 3
                        },
                        children: [
                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                sx: {
                                    flex: 1
                                },
                                children: [
                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                        variant: "h5",
                                        component: "div",
                                        gutterBottom: true,
                                        children: horse.name
                                    }),
                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                        sx: {
                                            display: "grid",
                                            gridTemplateColumns: "1fr 1fr",
                                            gap: 2,
                                            mb: 2
                                        },
                                        children: [
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "性別"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.sex
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "年齢"
                                                    }),
                                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: [
                                                            horse.age,
                                                            "歳"
                                                        ]
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "父"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.sire
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "母"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.dam
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "母の父"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.damsire
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "馬体重"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.weight ? `${horse.weight}kg` : "-"
                                                    })
                                                ]
                                            })
                                        ]
                                    }),
                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                        sx: {
                                            display: "grid",
                                            gridTemplateColumns: "1fr 1fr",
                                            gap: 2,
                                            mb: 2
                                        },
                                        children: [
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "賞金"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.race_records?.total_prize_money ? `${horse.race_records.total_prize_money.toLocaleString()}円` : "データなし"
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: horse.is_unsold ? "未落札" : "落札価格"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.sold_price !== null && horse.sold_price !== undefined ? `${horse.sold_price.toLocaleString()}円` : horse.is_unsold ? "未落札" : "データなし"
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "販売者"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.seller || "不明"
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "主取り"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.owner || "不明"
                                                    })
                                                ]
                                            }),
                                            horse.trainer && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "調教師"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: horse.trainer
                                                    })
                                                ]
                                            }),
                                            (horse.race_records?.starts !== undefined || horse.race_records?.wins !== undefined || horse.race_records?.seconds !== undefined || horse.race_records?.thirds !== undefined) && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "戦績"
                                                    }),
                                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: [
                                                            horse.race_records?.starts || 0,
                                                            "戦 ",
                                                            horse.race_records?.wins || 0,
                                                            "勝",
                                                            horse.race_records?.seconds !== undefined ? ` ${horse.race_records.seconds}着` : "",
                                                            horse.race_records?.thirds !== undefined ? `-${horse.race_records.thirds}着` : ""
                                                        ]
                                                    })
                                                ]
                                            }),
                                            /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "競走馬登録"
                                                    }),
                                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: [
                                                            horse.is_retired ? "引退" : horse.race_records?.starts !== undefined ? "登録済み" : "未登録",
                                                            horse.retirement_date && ` (${new Date(horse.retirement_date).getFullYear()}.${(new Date(horse.retirement_date).getMonth() + 1).toString().padStart(2, "0")}引退)`
                                                        ]
                                                    })
                                                ]
                                            }),
                                            horse.auction_date && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                children: [
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "subtitle2",
                                                        color: "text.secondary",
                                                        children: "オークション日"
                                                    }),
                                                    /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                        variant: "body1",
                                                        children: new Date(horse.auction_date).toLocaleDateString("ja-JP", {
                                                            year: "numeric",
                                                            month: "long",
                                                            day: "numeric",
                                                            weekday: "short"
                                                        })
                                                    })
                                                ]
                                            })
                                        ]
                                    }),
                                    horse.disease_tags && horse.disease_tags.length > 0 && /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                        sx: {
                                            mb: 2
                                        },
                                        children: [
                                            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Typography, {
                                                variant: "subtitle2",
                                                color: "error",
                                                children: "疾病情報"
                                            }),
                                            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                                sx: {
                                                    display: "flex",
                                                    gap: 1,
                                                    flexWrap: "wrap"
                                                },
                                                children: horse.disease_tags.map((disease, index)=>/*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Chip, {
                                                        label: disease,
                                                        color: "error",
                                                        size: "small"
                                                    }, index))
                                            })
                                        ]
                                    }),
                                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                        sx: {
                                            display: "flex",
                                            gap: 2,
                                            mt: 2
                                        },
                                        children: [
                                            horse.jbis_url && /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Button, {
                                                variant: "outlined",
                                                size: "small",
                                                href: horse.jbis_url,
                                                target: "_blank",
                                                rel: "noopener noreferrer",
                                                children: "JBIS"
                                            }),
                                            horse.auction_url && /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Button, {
                                                variant: "outlined",
                                                size: "small",
                                                href: horse.auction_url,
                                                target: "_blank",
                                                rel: "noopener noreferrer",
                                                children: "オークションページ"
                                            })
                                        ]
                                    })
                                ]
                            }),
                            horse.image_url && /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_3__.Box, {
                                sx: {
                                    width: 300,
                                    flexShrink: 0
                                },
                                children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("img", {
                                    src: horse.image_url,
                                    alt: horse.name,
                                    style: {
                                        width: "100%",
                                        height: "auto",
                                        borderRadius: "4px",
                                        objectFit: "cover"
                                    }
                                })
                            })
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
                                variant: "subtitle2",
                                color: "text.secondary",
                                gutterBottom: true,
                                children: "コメント"
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
    });
}


/***/ }),

/***/ 64181:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   $$typeof: () => (/* binding */ $$typeof),
/* harmony export */   __esModule: () => (/* binding */ __esModule),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var next_dist_build_webpack_loaders_next_flight_loader_module_proxy__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(61363);

const proxy = (0,next_dist_build_webpack_loaders_next_flight_loader_module_proxy__WEBPACK_IMPORTED_MODULE_0__.createProxy)(String.raw`/Users/yum.ishii/SaraokuDB/frontend/app/test-horse/page.tsx`)

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
var __webpack_require__ = require("../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, [587,668,717,610], () => (__webpack_exec__(1799)));
module.exports = __webpack_exports__;

})();