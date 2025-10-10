"use strict";
exports.id = 322;
exports.ids = [322];
exports.modules = {

/***/ 36681:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   T: () => (/* binding */ LoadingSpinner)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(75284);

const LoadingSpinner = ()=>/*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__/* .jsx */ .tZ("div", {
        className: "flex justify-center items-center h-64",
        children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__/* .jsx */ .tZ("div", {
            className: "animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"
        })
    });


/***/ }),

/***/ 97016:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Z: () => (/* binding */ HorseImage)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var next_image__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(52451);
/* harmony import */ var next_image__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(next_image__WEBPACK_IMPORTED_MODULE_1__);



function HorseImage({ src, alt, className = "", width = 300, height = 300 }) {
    const [imgSrc, setImgSrc] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(src);
    const [isLoading, setIsLoading] = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(true);
    return /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsxs */ .BX)("div", {
        className: `relative ${className}`,
        style: {
            width: "100%",
            height: "100%"
        },
        children: [
            /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ((next_image__WEBPACK_IMPORTED_MODULE_1___default()), {
                src: imgSrc,
                alt: alt,
                width: width,
                height: height,
                className: `w-full h-auto transition-opacity duration-300 ${isLoading ? "opacity-0" : "opacity-100"}`,
                style: {
                    width: "100%",
                    height: "auto"
                },
                onLoadingComplete: ()=>setIsLoading(false),
                onError: ()=>{
                    setImgSrc("/placeholder-horse.jpg");
                    setIsLoading(false);
                },
                loading: "lazy",
                unoptimized: "production" !== "production"
            }),
            isLoading && /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("div", {
                className: "absolute inset-0 flex items-center justify-center bg-gray-100",
                children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_2__/* .jsx */ .tZ("div", {
                    className: "animate-pulse text-gray-400",
                    children: "読み込み中..."
                })
            })
        ]
    });
}


/***/ }),

/***/ 9130:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   T: () => (/* binding */ LoadingSpinner)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(75193);
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__);

const LoadingSpinner = ()=>/*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__.jsx("div", {
        className: "flex justify-center items-center h-64",
        children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_0__.jsx("div", {
            className: "animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"
        })
    });


/***/ })

};
;