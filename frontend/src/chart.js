import Chart from "chart.js/auto";

export function createBarChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Data",
                    data: data,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                },
            },
        },
    });
}

export function createLineChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Trend",
                    data: data,
                    fill: false,
                    tension: 0.4,
                },
            ],
        },
        options: {
            responsive: true,
        },
    });
}