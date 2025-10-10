"use strict";
exports.id = 346;
exports.ids = [346];
exports.modules = {

/***/ 92346:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Z: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var next_link__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(11440);
/* harmony import */ var next_link__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(next_link__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(17421);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_mui_material__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(57114);
/* harmony import */ var next_navigation__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(next_navigation__WEBPACK_IMPORTED_MODULE_2__);





const HeaderCard = ({ jbisUrl, auctionUrl })=>{
    const router = (0,next_navigation__WEBPACK_IMPORTED_MODULE_2__.useRouter)();
    return /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ("header", {
        className: "bg-white shadow-sm border-b",
        children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ("div", {
            className: "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8",
            children: /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsxs */ .BX)("div", {
                className: "flex justify-between items-center py-4",
                children: [
                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsxs */ .BX)("button", {
                        onClick: ()=>router.back(),
                        className: "rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors flex items-center",
                        children: [
                            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ("svg", {
                                className: "w-5 h-5 mr-2",
                                fill: "none",
                                stroke: "currentColor",
                                viewBox: "0 0 24 24",
                                children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ("path", {
                                    strokeLinecap: "round",
                                    strokeLinejoin: "round",
                                    strokeWidth: 2,
                                    d: "M15 19l-7-7 7-7"
                                })
                            }),
                            "戻る"
                        ]
                    }),
                    /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsxs */ .BX)("div", {
                        className: "flex gap-4",
                        children: [
                            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_4__.Button, {
                                component: (next_link__WEBPACK_IMPORTED_MODULE_1___default()),
                                href: "/",
                                variant: "outlined",
                                className: "rounded-md bg-white border border-black text-black hover:bg-gray-100",
                                children: "解析"
                            }),
                            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__/* .jsx */ .tZ(_mui_material__WEBPACK_IMPORTED_MODULE_4__.Button, {
                                component: (next_link__WEBPACK_IMPORTED_MODULE_1___default()),
                                href: "/horses",
                                variant: "outlined",
                                className: "rounded-md bg-white border border-black text-black hover:bg-gray-100",
                                children: "直近の追加"
                            })
                        ]
                    })
                ]
            })
        })
    });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (HeaderCard);


/***/ })

};
;