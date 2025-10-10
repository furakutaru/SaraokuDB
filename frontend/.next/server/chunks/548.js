"use strict";
exports.id = 548;
exports.ids = [548];
exports.modules = {

/***/ 11548:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Z: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);


const HorseImage = ({ src, alt, fallbackSrc = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xOCAxM2gxLjY4M2MuNTU5IDAgLjk1Mi0uNTgxIC43ODctMS4xNDNsLTEuNjUxLTQuODU0YTEuNSAxLjUgMCAwIDAtMS40MDItMS4wNDNoLTguMzE0YTEuNSAxLjUgMCAwIDAtMS40MDIgMS4wNDNsLTEuNjUgNC44NTRjLS4xNjUuNTYyLjIyOCAxLjE0My43ODcgMS4xNDNIM2ExIDEgMCAwIDAtMSAxdjhhMSAxIDAgMCAwIDEgMWgxNGExIDEgMCAwIDAgMS0xdi04YTEgMSAwIDAgMC0xLTF6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+", className = "", width = 300, height = 200, ...props })=>{
    const [imgSrc, setImgSrc] = react__WEBPACK_IMPORTED_MODULE_0___default().useState(src || fallbackSrc);
    react__WEBPACK_IMPORTED_MODULE_0___default().useEffect(()=>{
        setImgSrc(src || fallbackSrc);
    }, [
        src,
        fallbackSrc
    ]);
    return /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_1__/* .jsx */ .tZ("div", {
        className: "relative w-full h-full",
        children: /*#__PURE__*/ _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_1__/* .jsx */ .tZ("img", {
            src: imgSrc,
            alt: alt,
            className: `object-cover ${className}`,
            width: width,
            height: height,
            onError: ()=>setImgSrc(fallbackSrc),
            ...props
        })
    });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (HorseImage);


/***/ })

};
;