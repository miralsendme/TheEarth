/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class TheEarthDashboard extends Component {
    static template = "travel_booking_management.Dashboard";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            hotelCount: 0,
            flightCount: 0,
            trainCount: 0,
            busCount: 0,
            carCount: 0,
            insuranceCount: 0,
            visaCount: 0,
            packageCount: 0,
            eventCount: 0,
            cancellationCount: 0,
            totalBookings: 0,
            totalRevenue: 0,
            todayDate: new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
            monthlyBookings: [],
            bookingByType: [],
        });
        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const [hotel, flight, intlFlight, train, bus, car, insurance, visa, pkg, event] = await Promise.all([
                this.orm.searchCount("travel.hotel.booking", []),
                this.orm.searchCount("travel.domestic.flight.booking", []),
                this.orm.searchCount("travel.international.flight.booking", []),
                this.orm.searchCount("travel.train.booking", []),
                this.orm.searchCount("travel.bus.booking", []),
                this.orm.searchCount("travel.car.booking", []),
                this.orm.searchCount("travel.insurance.booking", []),
                this.orm.searchCount("travel.visa.booking", []),
                this.orm.searchCount("travel.package.tour.booking", []),
                this.orm.searchCount("travel.event.booking", []),
            ]);

            // Cancellation counts
            const [hotelCancel, busCancel, trainCancel, domFlightCancel, intlFlightCancel, insCancel, visaCancel] = await Promise.all([
                this.orm.searchCount("travel.hotel.cancellation", []),
                this.orm.searchCount("travel.bus.cancellation", []),
                this.orm.searchCount("travel.train.cancellation", []),
                this.orm.searchCount("travel.domestic.flight.cancellation", []),
                this.orm.searchCount("travel.intl.flight.cancellation", []),
                this.orm.searchCount("travel.insurance.cancellation", []),
                this.orm.searchCount("travel.visa.cancellation", []),
            ]);

            // Revenue from hotel bookings
            const hotelRecords = await this.orm.searchRead("travel.hotel.booking", [], ["total_amount"]);
            const hotelRevenue = hotelRecords.reduce((sum, r) => sum + (r.total_amount || 0), 0);

            const flightRecords = await this.orm.searchRead("travel.domestic.flight.booking", [], ["total_amount"]);
            const flightRevenue = flightRecords.reduce((sum, r) => sum + (r.total_amount || 0), 0);

            const trainRecords = await this.orm.searchRead("travel.train.booking", [], ["total_amount"]);
            const trainRevenue = trainRecords.reduce((sum, r) => sum + (r.total_amount || 0), 0);

            const busRecords = await this.orm.searchRead("travel.bus.booking", [], ["total_amount"]);
            const busRevenue = busRecords.reduce((sum, r) => sum + (r.total_amount || 0), 0);

            this.state.hotelCount = hotel;
            this.state.flightCount = flight + intlFlight;
            this.state.trainCount = train;
            this.state.busCount = bus;
            this.state.carCount = car;
            this.state.insuranceCount = insurance;
            this.state.visaCount = visa;
            this.state.packageCount = pkg;
            this.state.eventCount = event;
            this.state.cancellationCount = hotelCancel + busCancel + trainCancel + domFlightCancel + intlFlightCancel + insCancel + visaCancel;
            this.state.totalRevenue = hotelRevenue + flightRevenue + trainRevenue + busRevenue;
            this.state.totalBookings = hotel + flight + intlFlight + train + bus + car + insurance + visa + pkg + event;

            this.state.bookingByType = [
                { label: "Hotel", count: hotel, color: "#667eea" },
                { label: "Flight", count: flight + intlFlight, color: "#f093fb" },
                { label: "Train", count: train, color: "#4facfe" },
                { label: "Bus", count: bus, color: "#43e97b" },
                { label: "Car", count: car, color: "#fa709a" },
                { label: "Insurance", count: insurance, color: "#a18cd1" },
                { label: "Visa", count: visa, color: "#fccb90" },
                { label: "Package", count: pkg, color: "#96fbc4" },
                { label: "Event", count: event, color: "#f5576c" },
            ];
        } catch (e) {
            console.error("Dashboard load error:", e);
        }
    }

    openBookings(model) {
        const modelMap = {
            hotel: { res_model: "travel.hotel.booking", name: "Hotel Bookings" },
            domestic_flight: { res_model: "travel.domestic.flight.booking", name: "Domestic Flight Bookings" },
            international_flight: { res_model: "travel.international.flight.booking", name: "International Flight Bookings" },
            train: { res_model: "travel.train.booking", name: "Train Bookings" },
            bus: { res_model: "travel.bus.booking", name: "Bus Bookings" },
            car: { res_model: "travel.car.booking", name: "Car Bookings" },
            insurance: { res_model: "travel.insurance.booking", name: "Insurance Bookings" },
            visa: { res_model: "travel.visa.booking", name: "Visa Bookings" },
            package: { res_model: "travel.package.tour.booking", name: "Package Tour Bookings" },
            event: { res_model: "travel.event.booking", name: "Event Bookings" },
        };
        const m = modelMap[model];
        if (m) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: m.name,
                res_model: m.res_model,
                view_mode: "list,form",
                views: [[false, "list"], [false, "form"]],
                target: "current",
            });
        }
    }

    openCancellations() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Hotel Cancellations",
            res_model: "travel.hotel.cancellation",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openServiceCharges() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Service Charges",
            res_model: "travel.service.charge",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    formatCurrency(value) {
        return "₹ " + (value || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    getBarWidth(count) {
        const max = Math.max(...this.state.bookingByType.map(b => b.count), 1);
        return Math.round((count / max) * 100);
    }
}

registry.category("actions").add("travel_booking_management.dashboard", TheEarthDashboard);
