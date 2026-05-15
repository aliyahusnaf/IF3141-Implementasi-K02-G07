/** @odoo-module **/
import { Component, useState, onMounted, onPatched, useRef, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class M4FRDashboard extends Component {
    static template = "m4fr.Dashboard";

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            period: "this_month",
            loading: true,
            kpi: {
                total_pendapatan: 0,
                total_pengeluaran: 0,
                laba_bersih: 0,
                pesanan_selesai: 0,
                nilai_stok: 0,
            },
        });
        this._chartData = null;
        this._charts = {};

        this.revenueRef = useRef("revenueChart");
        this.profitRef = useRef("profitChart");
        this.expenseRef = useRef("expenseChart");

        onMounted(() => this.loadDashboard());
        onPatched(() => this._renderChartsIfReady());
        onWillUnmount(() => this._destroyCharts());
    }

    async _getChartLib() {
        if (!window.Chart) {
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js");
        }
        return window.Chart;
    }

    async loadDashboard() {
        this._destroyCharts();
        this.state.loading = true;

        const [kpi, revenue, profit, expense] = await Promise.all([
            this.rpc("/m4fr/dashboard/kpi", { period: this.state.period }),
            this.rpc("/m4fr/dashboard/chart/revenue", { period: this.state.period }),
            this.rpc("/m4fr/dashboard/chart/profit", { period: this.state.period }),
            this.rpc("/m4fr/dashboard/chart/expense-breakdown", { period: this.state.period }),
        ]);

        this.state.kpi = kpi;
        this._chartData = { revenue, profit, expense };
        this.state.loading = false;
    }

    async _renderChartsIfReady() {
        if (this.state.loading || !this._chartData) return;
        const data = this._chartData;
        this._chartData = null;

        const Chart = await this._getChartLib();
        this._renderRevenueChart(data.revenue, Chart);
        this._renderProfitChart(data.profit, Chart);
        this._renderExpenseChart(data.expense, Chart);
    }

    _renderRevenueChart(data, Chart) {
        const canvas = this.revenueRef.el;
        if (!canvas) return;
        if (this._charts.revenue) this._charts.revenue.destroy();
        this._charts.revenue = new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map((d) => d.bulan),
                datasets: [
                    {
                        label: "Pendapatan",
                        data: data.map((d) => d.pendapatan),
                        backgroundColor: "rgba(54, 162, 235, 0.7)",
                    },
                    {
                        label: "Pengeluaran",
                        data: data.map((d) => d.pengeluaran),
                        backgroundColor: "rgba(255, 99, 132, 0.7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { tooltip: { mode: "index", intersect: false } },
            },
        });
    }

    _renderProfitChart(data, Chart) {
        const canvas = this.profitRef.el;
        if (!canvas) return;
        if (this._charts.profit) this._charts.profit.destroy();
        this._charts.profit = new Chart(canvas, {
            type: "line",
            data: {
                labels: data.map((d) => d.bulan),
                datasets: [
                    {
                        label: "Laba Bersih",
                        data: data.map((d) => d.laba),
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        fill: true,
                        tension: 0.3,
                    },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false },
        });
    }

    _renderExpenseChart(data, Chart) {
        const canvas = this.expenseRef.el;
        if (!canvas) return;
        if (this._charts.expense) this._charts.expense.destroy();
        this._charts.expense = new Chart(canvas, {
            type: "pie",
            data: {
                labels: data.map((d) => d.kategori),
                datasets: [
                    {
                        data: data.map((d) => d.jumlah),
                        backgroundColor: [
                            "rgba(255, 99, 132, 0.7)",
                            "rgba(54, 162, 235, 0.7)",
                            "rgba(255, 205, 86, 0.7)",
                            "rgba(75, 192, 192, 0.7)",
                        ],
                    },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false },
        });
    }

    _destroyCharts() {
        Object.values(this._charts).forEach((c) => c.destroy());
        this._charts = {};
    }

    async onPeriodChange(ev) {
        this.state.period = ev.target.value;
        await this.loadDashboard();
    }

    formatCurrency(val) {
        return "Rp " + new Intl.NumberFormat("id-ID").format(val);
    }
}

registry.category("actions").add("m4fr_dashboard", M4FRDashboard);
