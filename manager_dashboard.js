const API_BASE_URL = "http://127.0.0.1:8000";

const charts = {};

let allCustomers = [];
let filteredCustomers = [];

let currentPage = 1;


/* =========================================================
   HELPERS
========================================================= */

const $ = (id) =>
    document.getElementById(id);


function numberFormat(value) {

    return Number(value ?? 0)
        .toLocaleString("en-IN");
}


function currencyFormat(value) {

    return "₹" +
        Number(value ?? 0)
            .toLocaleString(
                "en-IN",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            );
}


function percentFormat(value) {

    return (
        Number(value ?? 0) * 100
    ).toFixed(2) + "%";
}


function safe(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return String(value);
}


function dateFormat(value) {

    if (!value) {
        return "—";
    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return String(value);
    }

    return date.toLocaleString(
        "en-IN"
    );
}


function themeValue(variable) {

    return getComputedStyle(
        document.documentElement
    )
        .getPropertyValue(variable)
        .trim();
}


/* =========================================================
   API
========================================================= */

async function getJSON(endpoint) {

    const response =
        await fetch(
            API_BASE_URL + endpoint
        );

    if (!response.ok) {

        let message =
            `Request failed (${response.status})`;

        try {

            const data =
                await response.json();

            message =
                data.detail ||
                message;

        } catch (_) {
        }

        throw new Error(message);
    }

    return await response.json();
}


/* =========================================================
   API STATUS
========================================================= */

async function checkAPI() {

    try {

        await getJSON("/");

        $("apiStatus").textContent =
            "API connected";

        $("statusDot").className =
            "status-dot online";

    } catch (error) {

        console.error(error);

        $("apiStatus").textContent =
            "API unavailable";

        $("statusDot").className =
            "status-dot offline";
    }
}


/* =========================================================
   CHART MANAGEMENT
========================================================= */

function destroyChart(name) {

    if (charts[name]) {

        charts[name].destroy();

        charts[name] = null;
    }
}


function createBarChart(
    canvasId,
    labels,
    values,
    name,
    showPercent = true
) {

    const canvas =
        $(canvasId);

    if (!canvas) {
        return;
    }

    destroyChart(name);


    charts[name] =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels,

                    datasets: [

                        {
                            data: values,

                            backgroundColor:
                                themeValue(
                                    "--accent"
                                ),

                            borderWidth:
                                0,

                            maxBarThickness:
                                34
                        }

                    ]
                },


                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    plugins: {

                        legend: {
                            display:
                                false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function (
                                        context
                                    ) {

                                        return showPercent
                                            ? percentFormat(
                                                context.raw
                                            )
                                            : numberFormat(
                                                context.raw
                                            );
                                    }
                            }
                        }
                    },


                    scales: {

                        x: {

                            grid: {
                                display:
                                    false
                            },

                            ticks: {

                                color:
                                    themeValue(
                                        "--muted"
                                    ),

                                maxRotation:
                                    30
                            }
                        },


                        y: {

                            beginAtZero:
                                true,

                            suggestedMax:
                                showPercent
                                    ? 1
                                    : undefined,

                            grid: {

                                color:
                                    themeValue(
                                        "--line"
                                    )
                            },

                            ticks: {

                                color:
                                    themeValue(
                                        "--muted"
                                    ),

                                callback:
                                    function (
                                        value
                                    ) {

                                        return showPercent
                                            ? Math.round(
                                                value * 100
                                            ) + "%"
                                            : numberFormat(
                                                value
                                            );
                                    }
                            }
                        }
                    }
                }
            }
        );
}


/* =========================================================
   SUMMARY
========================================================= */

async function loadSummary() {

    const data =
        await getJSON(
            "/dashboard/summary"
        );


    $("totalCustomers").textContent =
        numberFormat(
            data.total_customers
        );


    $("churnRate").textContent =
        percentFormat(
            data.churn_rate
        );


    $("highRiskCustomers").textContent =
        numberFormat(
            data.high_risk_customers
        );


    $("totalPredictedLtv").textContent =
        currencyFormat(
            data.total_predicted_ltv
        );


    $("avgPredictedLtv").textContent =
        currencyFormat(
            data.avg_predicted_ltv
        );


    $("avgMonthlyCharges").textContent =
        currencyFormat(
            data.avg_monthly_charges
        );


    $("lastUpdated").textContent =
        "Updated " +
        new Date().toLocaleString(
            "en-IN"
        );


    return data;
}


/* =========================================================
   EXECUTIVE INSIGHTS
========================================================= */

async function loadExecutiveInsights() {

    const data =
        await getJSON(
            "/dashboard/executive-insights"
        );


    const headline =
        data.headline || {};

    const contract =
        data.largest_contract_risk || {};

    const service =
        data.service_gap || {};


    $("biggestRiskText").textContent =
        safe(
            contract.segment
        );


    $("biggestRiskDetail").textContent =

        contract.churn_rate != null
            ? `${percentFormat(
                contract.churn_rate
            )} observed churn within this segment`
            : "No segment signal available";


    $("revenueRiskText").textContent =
        currencyFormat(
            headline.high_risk_ltv
        );


    $("revenueRiskDetail").textContent =

        `${numberFormat(
            headline.high_risk_customers
        )} customers above 70% risk`;


    $("serviceGapText").textContent =
        safe(
            service.service
        );


    $("serviceGapDetail").textContent =

        service.churn_rate_without_service != null
            ? `${percentFormat(
                service.churn_rate_without_service
            )} observed churn without this service`
            : "No service signal available";


    $("priorityText").textContent =
        numberFormat(
            headline.priority_customers
        );


    $("priorityDetail").textContent =
        "High risk + high predicted LTV";
}


/* =========================================================
   REVENUE EXPOSURE
========================================================= */

async function loadRevenueRisk() {

    const data =
        await getJSON(
            "/dashboard/revenue-at-risk"
        );


    const high =
        Number(
            data.high_risk_ltv || 0
        );

    const medium =
        Number(
            data.medium_risk_ltv || 0
        );

    const low =
        Number(
            data.low_risk_ltv || 0
        );

    const total =
        Number(
            data.total_ltv ||
            high +
            medium +
            low
        );


    $("highRiskLtv").textContent =
        currencyFormat(high);

    $("mediumRiskLtv").textContent =
        currencyFormat(medium);

    $("lowRiskLtv").textContent =
        currencyFormat(low);

    $("revenueTotalLtv").textContent =
        currencyFormat(total);


    $("highRiskBar").style.width =
        total
            ? `${high / total * 100}%`
            : "0%";


    $("mediumRiskBar").style.width =
        total
            ? `${medium / total * 100}%`
            : "0%";


    $("lowRiskBar").style.width =
        total
            ? `${low / total * 100}%`
            : "0%";
}


/* =========================================================
   CHURN OUTCOME
========================================================= */

function renderOutcomeChart(
    summaryData
) {

    const canvas =
        $("churnOutcomeChart");

    if (!canvas) {
        return;
    }


    destroyChart("outcome");


    const churn =
        Number(
            summaryData.churn_customers ||
            0
        );


    const retained =
        Number(
            summaryData.retained_customers ??
            (
                summaryData.total_customers -
                churn
            )
        );


    charts.outcome =
        new Chart(
            canvas,
            {

                type: "doughnut",

                data: {

                    labels: [
                        "Retained",
                        "Churn"
                    ],

                    datasets: [

                        {
                            data: [
                                retained,
                                churn
                            ],

                            backgroundColor: [
                                themeValue(
                                    "--success"
                                ),

                                themeValue(
                                    "--danger"
                                )
                            ],

                            borderWidth:
                                0
                        }

                    ]
                },


                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    cutout:
                        "70%",

                    plugins: {

                        legend: {

                            position:
                                "bottom",

                            labels: {

                                color:
                                    themeValue(
                                        "--text"
                                    )
                            }
                        }
                    }
                }
            }
        );
}


/* =========================================================
   RISK DISTRIBUTION
========================================================= */

async function loadRiskChart() {

    const data =
        await getJSON(
            "/dashboard/churn-risk"
        );


    const rows =
        data.risk_distribution ||
        [];


    createBarChart(
        "churnRiskChart",

        rows.map(
            item =>
                item.risk_level
        ),

        rows.map(
            item =>
                Number(
                    item.customer_count ||
                    0
                )
        ),

        "risk",

        false
    );
}


/* =========================================================
   LTV
========================================================= */

async function loadLtvChart() {

    const data =
        await getJSON(
            "/dashboard/ltv-segments"
        );


    const rows =
        data.ltv_segments ||
        [];


    createBarChart(
        "ltvSegmentChart",

        rows.map(
            item =>
                item.ltv_segment
        ),

        rows.map(
            item =>
                Number(
                    item.customer_count ||
                    0
                )
        ),

        "ltv",

        false
    );
}


/* =========================================================
   SEGMENT CHARTS
========================================================= */

async function loadSegmentChart(
    endpoint,
    canvasId,
    chartName,
    field
) {

    const data =
        await getJSON(
            endpoint
        );


    const rows =
        data.data ||
        [];


    createBarChart(
        canvasId,

        rows.map(
            item =>
                safe(
                    item[field]
                )
        ),

        rows.map(
            item =>
                Number(
                    item.churn_rate ||
                    0
                )
        ),

        chartName,

        true
    );
}


/* =========================================================
   RISK x LTV
========================================================= */

async function loadRiskLtvChart() {

    try {

        const data =
            await getJSON(
                "/dashboard/risk-ltv-matrix"
            );


        const rows =
            data.customers ||
            data.data ||
            [];


        if (
            rows.length === 0
        ) {
            return;
        }


        const canvas =
            $("riskLtvChart");


        if (!canvas) {
            return;
        }


        destroyChart(
            "riskLtv"
        );


        charts.riskLtv =
            new Chart(
                canvas,
                {

                    type: "scatter",

                    data: {

                        datasets: [

                            {
                                data:

                                    rows.map(
                                        item => ({

                                            x:
                                                Number(
                                                    item.churn_probability ||
                                                    0
                                                ) * 100,

                                            y:
                                                Number(
                                                    item.predicted_ltv ||
                                                    0
                                                )
                                        })
                                    ),

                                backgroundColor:
                                    themeValue(
                                        "--accent"
                                    ),

                                pointRadius:
                                    3,

                                pointHoverRadius:
                                    5
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {
                                display:
                                    false
                            },

                            tooltip: {

                                callbacks: {

                                    label:
                                        function (
                                            context
                                        ) {

                                            return (
                                                "Risk " +
                                                Number(
                                                    context.parsed.x
                                                ).toFixed(1) +
                                                "% · LTV " +
                                                currencyFormat(
                                                    context.parsed.y
                                                )
                                            );
                                        }
                                }
                            }
                        },


                        scales: {

                            x: {

                                title: {

                                    display:
                                        true,

                                    text:
                                        "Churn probability (%)",

                                    color:
                                        themeValue(
                                            "--muted"
                                        )
                                },

                                grid: {

                                    color:
                                        themeValue(
                                            "--line"
                                        )
                                },

                                ticks: {

                                    color:
                                        themeValue(
                                            "--muted"
                                        )
                                }
                            },


                            y: {

                                title: {

                                    display:
                                        true,

                                    text:
                                        "Predicted LTV",

                                    color:
                                        themeValue(
                                            "--muted"
                                        )
                                },

                                grid: {

                                    color:
                                        themeValue(
                                            "--line"
                                        )
                                },

                                ticks: {

                                    color:
                                        themeValue(
                                            "--muted"
                                        )
                                }
                            }
                        }
                    }
                }
            );

    } catch (error) {

        console.warn(
            "Risk × LTV endpoint unavailable:",
            error.message
        );
    }
}


/* =========================================================
   MONTHLY CHARGE BAND
========================================================= */

async function loadChargeChart() {

    try {

        const data =
            await getJSON(
                "/dashboard/churn-by-charges"
            );


        const rows =
            data.data ||
            [];


        createBarChart(
            "chargeBandChart",

            rows.map(
                row =>
                    row.charge_band
            ),

            rows.map(
                row =>
                    Number(
                        row.churn_rate ||
                        0
                    )
            ),

            "chargeBand",

            true
        );

    } catch (error) {

        console.warn(
            "Charge-band chart unavailable:",
            error.message
        );
    }
}


/* =========================================================
   CUSTOMER RISK INDICATORS
========================================================= */

function getRiskIndicators(
    customer
) {

    const indicators = [];


    if (
        customer.contract ===
        "Month-to-month"
    ) {

        indicators.push(
            "Month-to-month contract"
        );
    }


    if (
        customer.tenure != null &&
        Number(customer.tenure) <= 12
    ) {

        indicators.push(
            "Early tenure"
        );
    }


    if (
        customer.onlinesecurity ===
        "No"
    ) {

        indicators.push(
            "No online security"
        );
    }


    if (
        customer.techsupport ===
        "No"
    ) {

        indicators.push(
            "No tech support"
        );
    }


    if (
        customer.paymentmethod ===
        "Electronic check"
    ) {

        indicators.push(
            "Electronic check"
        );
    }


    if (
        customer.monthlycharges != null &&
        Number(customer.monthlycharges) >= 80
    ) {

        indicators.push(
            "High monthly charge"
        );
    }


    if (
        customer.internetservice ===
        "Fiber optic"
    ) {

        indicators.push(
            "Fiber optic service"
        );
    }


    return indicators.slice(
        0,
        5
    );
}


/* =========================================================
   PRIORITY CUSTOMERS
========================================================= */

async function loadPriorityCustomers() {

    const data =
        await getJSON(
            "/dashboard/priority-customers"
        );


    const customers =
        (
            data.priority_customers ||
            []
        ).slice(
            0,
            2
        );


    const container =
        $("priorityCards");


    if (
        customers.length ===
        0
    ) {

        container.innerHTML =

            `<div class="panel muted">
                No current priority customers.
            </div>`;

        return;
    }


    container.innerHTML =
        customers.map(
            customer => {

                const probability =
                    Number(
                        customer.churn_probability ||
                        0
                    );


                const reasons =
                    getRiskIndicators(
                        customer
                    );


                return `

                    <article
                        class="panel priority-card"
                        data-customer-id="${safe(
                            customer.customerid
                        )}"
                    >

                        <div class="priority-header">

                            <div>

                                <span class="eyebrow">
                                    PRIORITY CUSTOMER
                                </span>

                                <div class="priority-id">
                                    ${safe(
                                        customer.customerid
                                    )}
                                </div>

                                <div class="priority-sub">
                                    ${safe(
                                        customer.contract
                                    )}
                                </div>

                            </div>


                            <div class="priority-score">

                                <strong>
                                    ${percentFormat(
                                        probability
                                    )}
                                </strong>

                                <small>
                                    churn probability
                                </small>

                            </div>

                        </div>


                        <div class="priority-metrics">

                            <div>

                                <span>
                                    Predicted LTV
                                </span>

                                <strong>
                                    ${currencyFormat(
                                        customer.predicted_ltv
                                    )}
                                </strong>

                            </div>


                            <div>

                                <span>
                                    Tenure
                                </span>

                                <strong>
                                    ${safe(
                                        customer.tenure
                                    )} months
                                </strong>

                            </div>


                            <div>

                                <span>
                                    Monthly charge
                                </span>

                                <strong>
                                    ${currencyFormat(
                                        customer.monthlycharges
                                    )}
                                </strong>

                            </div>

                        </div>


                        <div class="priority-reasons">

                            <div class="priority-reasons-title">
                                PROFILE INDICATORS
                            </div>

                            <div class="risk-chips">

                                ${
                                    reasons.length
                                    ?

                                    reasons.map(
                                        reason =>
                                            `<span>
                                                ${reason}
                                            </span>`
                                    ).join("")

                                    :

                                    `<span>
                                        No configured indicators
                                    </span>`
                                }

                            </div>

                        </div>

                    </article>
                `;
            }
        ).join("");


    container
        .querySelectorAll(
            "[data-customer-id]"
        )
        .forEach(
            card => {

                card.addEventListener(
                    "click",
                    () =>
                        loadCustomerDetail(
                            card.dataset.customerId
                        )
                );
            }
        );
}


/* =========================================================
   CUSTOMER SEARCH
========================================================= */

function customerSearchText(
    customer
) {

    return [

        customer.customerid,

        customer.contract,

        customer.paymentmethod,

        customer.internetservice,

        customer.tenuregroup,

        customer.gender,

        customer.churn

    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
}


function applyFilters() {

    const query =
        $("customerSearchInput")
            .value
            .trim()
            .toLowerCase();


    const risk =
        $("riskFilter")
            .value;


    filteredCustomers =
        allCustomers.filter(
            customer => {

                const probability =
                    Number(
                        customer.churn_probability ||
                        0
                    );


                const matchesQuery =

                    !query ||

                    customerSearchText(
                        customer
                    ).includes(
                        query
                    );


                const matchesRisk =

                    risk === "all" ||

                    (
                        risk === "high" &&
                        probability >= 0.70
                    ) ||

                    (
                        risk === "medium" &&
                        probability >= 0.40 &&
                        probability < 0.70
                    ) ||

                    (
                        risk === "low" &&
                        probability < 0.40
                    );


                return (
                    matchesQuery &&
                    matchesRisk
                );
            }
        );


    currentPage = 1;

    renderCustomerTable();
}


/* =========================================================
   CUSTOMER TABLE
========================================================= */

function renderCustomerTable() {

    const pageSize =
        Number(
            $("pageSize").value
        );


    const start =
        (
            currentPage - 1
        ) * pageSize;


    const rows =
        filteredCustomers.slice(
            start,
            start + pageSize
        );


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                filteredCustomers.length /
                pageSize
            )
        );


    const tbody =
        $("customerTableBody");


    if (
        rows.length ===
        0
    ) {

        tbody.innerHTML =

            `<tr>
                <td
                    colspan="8"
                    class="empty-cell"
                >
                    No matching customers.
                </td>
            </tr>`;

    } else {

        tbody.innerHTML =

            rows.map(
                customer => {

                    const probability =
                        Number(
                            customer.churn_probability ||
                            0
                        );


                    let riskClass =
                        "risk-low";


                    if (
                        probability >=
                        0.70
                    ) {

                        riskClass =
                            "risk-high";

                    } else if (
                        probability >=
                        0.40
                    ) {

                        riskClass =
                            "risk-medium";
                    }


                    return `

                        <tr
                            data-customer-id="${safe(
                                customer.customerid
                            )}"
                        >

                            <td>
                                ${safe(
                                    customer.customerid
                                )}
                            </td>

                            <td
                                class="${riskClass}"
                            >
                                ${percentFormat(
                                    probability
                                )}
                            </td>

                            <td>
                                ${currencyFormat(
                                    customer.predicted_ltv
                                )}
                            </td>

                            <td>
                                ${safe(
                                    customer.contract
                                )}
                            </td>

                            <td>
                                ${safe(
                                    customer.tenure
                                )} mo
                            </td>

                            <td>
                                ${currencyFormat(
                                    customer.monthlycharges
                                )}
                            </td>

                            <td>
                                ${safe(
                                    customer.internetservice
                                )}
                            </td>

                            <td
                                class="${
                                    customer.churn === "Yes"
                                    ? "churn-yes"
                                    : "churn-no"
                                }"
                            >
                                ${safe(
                                    customer.churn
                                )}
                            </td>

                        </tr>
                    `;
                }
            ).join("");
    }


    tbody
        .querySelectorAll(
            "[data-customer-id]"
        )
        .forEach(
            row => {

                row.addEventListener(
                    "click",
                    () =>
                        loadCustomerDetail(
                            row.dataset.customerId
                        )
                );
            }
        );


    $("pageInfo").textContent =

        `Page ${currentPage} of ${totalPages} · ` +
        `${numberFormat(
            filteredCustomers.length
        )} records`;


    $("prevPage").disabled =
        currentPage <= 1;


    $("nextPage").disabled =
        currentPage >= totalPages;
}


/* =========================================================
   LOAD ALL CUSTOMERS
========================================================= */

async function loadCustomers() {

    const data =
        await getJSON(
            "/dashboard/customers?limit=10000&offset=0"
        );


    allCustomers =
        data.customers ||
        [];


    filteredCustomers =
        allCustomers;


    $("customerCountLabel").textContent =

        `${numberFormat(
            data.total_count ??
            allCustomers.length
        )} records available`;


    renderCustomerTable();
}


/* =========================================================
   CUSTOMER DETAIL
========================================================= */

async function loadCustomerDetail(
    customerId
) {

    try {

        const result =
            await getJSON(
                `/dashboard/customer/${encodeURIComponent(
                    customerId
                )}`
            );


        const customer =
            result.customer ||
            {};


        $("selectedCustomerTitle")
            .textContent =
            safe(
                customer.customerid
            );


        $("searchMessage")
            .textContent =
            "Customer profile and model prediction";


        const fieldMap = {

            detailCustomerId:
                "customerid",

            detailGender:
                "gender",

            detailSeniorCitizen:
                "seniorcitizen",

            detailPartner:
                "partner",

            detailDependents:
                "dependents",

            detailTenure:
                "tenure",

            detailTenureGroup:
                "tenuregroup",

            detailPhoneService:
                "phoneservice",

            detailMultipleLines:
                "multiplelines",

            detailInternetService:
                "internetservice",

            detailOnlineSecurity:
                "onlinesecurity",

            detailOnlineBackup:
                "onlinebackup",

            detailDeviceProtection:
                "deviceprotection",

            detailTechSupport:
                "techsupport",

            detailStreamingTV:
                "streamingtv",

            detailStreamingMovies:
                "streamingmovies",

            detailTotalServices:
                "totalservices",

            detailContract:
                "contract",

            detailPaymentMethod:
                "paymentmethod",

            detailPaperlessBilling:
                "paperlessbilling",

            detailChurn:
                "churn"
        };


        Object.entries(
            fieldMap
        )
            .forEach(
                ([elementId, field]) => {

                    const element =
                        $(elementId);

                    if (element) {

                        element.textContent =
                            safe(
                                customer[field]
                            );
                    }
                }
            );


        $("detailMonthlyCharges")
            .textContent =
            currencyFormat(
                customer.monthlycharges
            );


        $("detailTotalCharges")
            .textContent =
            currencyFormat(
                customer.totalcharges
            );


        $("detailChurnProbability")
            .textContent =
            percentFormat(
                customer.churn_probability
            );


        $("detailPredictedLtv")
            .textContent =
            currencyFormat(
                customer.predicted_ltv
            );


        $("detailPredictionAt")
            .textContent =
            dateFormat(
                customer.prediction_at
            );


        const probability =
            Number(
                customer.churn_probability ||
                0
            );


        const badge =
            $("detailChurnBadge");


        if (
            probability >= 0.70
        ) {

            badge.textContent =
                "High risk";

            badge.className =
                "risk-badge high";

        } else if (
            probability >= 0.40
        ) {

            badge.textContent =
                "Medium risk";

            badge.className =
                "risk-badge medium";

        } else {

            badge.textContent =
                "Low risk";

            badge.className =
                "risk-badge low";
        }


        const indicators =
            getRiskIndicators(
                customer
            );


        $("riskDrivers")
            .innerHTML =

            indicators.length

                ?

                indicators.map(
                    item =>
                        `<span>
                            ${item}
                        </span>`
                ).join("")

                :

                `<span>
                    No configured profile indicators
                </span>`;


        document
            .querySelector(
                "#customer-detail"
            )
            .scrollIntoView({
                behavior:
                    "smooth"
            });

    } catch (error) {

        console.error(
            error
        );

        $("searchMessage")
            .textContent =
            error.message;
    }
}


/* =========================================================
   THEME
========================================================= */

function initTheme() {

    const savedTheme =
        localStorage.getItem(
            "dashboardTheme"
        ) ||
        "light";


    document.documentElement
        .setAttribute(
            "data-theme",
            savedTheme
        );


    $("themeToggle")
        .textContent =
        savedTheme === "dark"
            ? "Light"
            : "Dark";
}


function toggleTheme() {

    const current =
        document.documentElement
            .getAttribute(
                "data-theme"
            );


    const next =
        current === "dark"
            ? "light"
            : "dark";


    document.documentElement
        .setAttribute(
            "data-theme",
            next
        );


    localStorage.setItem(
        "dashboardTheme",
        next
    );


    $("themeToggle")
        .textContent =
        next === "dark"
            ? "Light"
            : "Dark";


    /*
       Rebuild charts so Chart.js picks up
       the new text/grid colors.
    */

    loadDashboard();
}


/* =========================================================
   DASHBOARD LOAD
========================================================= */

async function loadDashboard() {

    await checkAPI();


    const summaryData =
        await loadSummary();


    const tasks = [

        loadExecutiveInsights(),

        loadRevenueRisk(),

        Promise.resolve(
            renderOutcomeChart(
                summaryData
            )
        ),

        loadRiskChart(),

        loadLtvChart(),

        loadRiskLtvChart(),

        loadChargeChart(),

        loadSegmentChart(
            "/dashboard/churn-by-contract",
            "contractChart",
            "contract",
            "contract"
        ),

        loadSegmentChart(
            "/dashboard/churn-by-tenure",
            "tenureChart",
            "tenure",
            "tenure_segment"
        ),

        loadSegmentChart(
            "/dashboard/churn-by-internet",
            "internetChart",
            "internet",
            "internet_service"
        ),

        loadSegmentChart(
            "/dashboard/churn-by-payment",
            "paymentChart",
            "payment",
            "payment_method"
        ),

        loadSegmentChart(
            "/dashboard/churn-by-services",
            "servicesChart",
            "services",
            "total_services"
        ),

        loadSegmentChart(
            "/dashboard/churn-by-gender",
            "genderChart",
            "gender",
            "gender"
        ),

        loadPriorityCustomers(),

        loadCustomers()
    ];


    const results =
        await Promise.allSettled(
            tasks
        );


    results.forEach(
        result => {

            if (
                result.status ===
                "rejected"
            ) {

                console.error(
                    "Dashboard task failed:",
                    result.reason
                );
            }
        }
    );
}


/* =========================================================
   EVENTS
========================================================= */

$("refreshButton")
    .addEventListener(
        "click",
        loadDashboard
    );


$("themeToggle")
    .addEventListener(
        "click",
        toggleTheme
    );


$("searchTableButton")
    .addEventListener(
        "click",
        applyFilters
    );


$("customerSearchInput")
    .addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                applyFilters();
            }
        }
    );


$("riskFilter")
    .addEventListener(
        "change",
        applyFilters
    );


$("pageSize")
    .addEventListener(
        "change",
        () => {

            currentPage = 1;

            renderCustomerTable();
        }
    );


$("prevPage")
    .addEventListener(
        "click",
        () => {

            if (
                currentPage > 1
            ) {

                currentPage--;

                renderCustomerTable();
            }
        }
    );


$("nextPage")
    .addEventListener(
        "click",
        () => {

            const pageSize =
                Number(
                    $("pageSize").value
                );


            const totalPages =
                Math.max(
                    1,
                    Math.ceil(
                        filteredCustomers.length /
                        pageSize
                    )
                );


            if (
                currentPage <
                totalPages
            ) {

                currentPage++;

                renderCustomerTable();
            }
        }
    );


/* =========================================================
   START
========================================================= */

initTheme();

window.addEventListener(
    "load",
    loadDashboard
);