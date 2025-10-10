"use strict";
exports.id = 584;
exports.ids = [584];
exports.modules = {

/***/ 27584:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Z: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(75284);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(18038);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);


const SexBadge = ({ sex, age, className = "" })=>{
    const getSexInfo = (sexData)=>{
        console.log("Raw sex data:", sexData);
        if (!sexData) return {
            label: "-",
            color: "bg-gray-100 text-gray-800"
        };
        let sexStr = "";
        try {
            // 文字列の場合
            if (typeof sexData === "string") {
                // すでに「牡」「牝」「セ」が含まれている場合はそのまま使用
                if (sexData.includes("牡") || sexData.includes("牝") || sexData.includes("セ")) {
                    sexStr = sexData;
                } else if (sexData.startsWith("[") || sexData.startsWith('"')) {
                    // エスケープされた引用符を処理
                    const cleanStr = sexData.replace(/\\"/g, '"');
                    // JSONパースを試みる
                    try {
                        const parsed = JSON.parse(cleanStr);
                        sexStr = Array.isArray(parsed) ? parsed[0] : parsed;
                    } catch (e) {
                        console.error("JSON parse error:", e);
                        sexStr = sexData;
                    }
                } else {
                    sexStr = sexData;
                }
            } else if (Array.isArray(sexData)) {
                sexStr = sexData[0] || "";
            }
            // ユニコードエスケープシーケンスをデコード
            if (typeof sexStr === "string") {
                sexStr = sexStr.replace(/\\u([\dA-F]{4})/gi, (match, grp)=>{
                    return String.fromCharCode(parseInt(grp, 16));
                });
            }
            console.log("Processed sex string:", sexStr);
            // 性別の判定
            if (sexStr.includes("牡")) {
                return {
                    label: "牡",
                    color: "bg-blue-100 text-blue-800"
                };
            } else if (sexStr.includes("牝")) {
                return {
                    label: "牝",
                    color: "bg-pink-100 text-pink-800"
                };
            } else if (sexStr.includes("セ")) {
                return {
                    label: "セ",
                    color: "bg-green-100 text-green-800"
                };
            }
        } catch (e) {
            console.error("性別データの処理エラー:", e, "元の値:", sexData);
        }
        return {
            label: sexStr || "-",
            color: "bg-gray-100 text-gray-800"
        };
    };
    const sexInfo = getSexInfo(sex);
    const ageText = age ? `${age}歳` : "";
    return /*#__PURE__*/ (0,_emotion_react_jsx_runtime__WEBPACK_IMPORTED_MODULE_1__/* .jsxs */ .BX)("div", {
        className: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${sexInfo.color} ${className}`,
        children: [
            sexInfo.label,
            " ",
            ageText
        ]
    });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (SexBadge);


/***/ })

};
;