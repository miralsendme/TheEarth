/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef, onMounted, onWillUnmount, onWillUpdateProps } from "@odoo/owl";

// ─── Text field version (textarea) for passenger_names / guest_names ───
class PassengerAutocomplete extends Component {
    static template = "travel_booking_management.PassengerAutocomplete";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            suggestions: [],
            showDropdown: false,
            selectedIndex: -1,
            value: this.props.record.data[this.props.name] || "",
        });
        this.textareaRef = useRef("textarea");
        this.dropdownRef = useRef("dropdown");
        this._searchTimeout = null;
        this._onDocClick = this._onDocumentClick.bind(this);

        onMounted(() => {
            document.addEventListener("click", this._onDocClick);
            // Sync textarea value
            if (this.textareaRef.el) {
                this.textareaRef.el.value = this.state.value;
            }
        });
        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocClick);
            if (this._searchTimeout) clearTimeout(this._searchTimeout);
        });
        onWillUpdateProps((nextProps) => {
            this.state.value = nextProps.record.data[nextProps.name] || "";
        });
    }

    _onDocumentClick(ev) {
        if (this.dropdownRef.el && !this.dropdownRef.el.contains(ev.target)) {
            this.state.showDropdown = false;
        }
    }

    get isReadonly() {
        return this.props.readonly;
    }

    onInput(ev) {
        const textarea = ev.target;
        const value = textarea.value;
        this.state.value = value;
        this.props.record.update({ [this.props.name]: value });

        const cursorPos = textarea.selectionStart;
        const beforeCursor = value.substring(0, cursorPos);
        const lastNewline = beforeCursor.lastIndexOf("\n");
        const currentLine = beforeCursor.substring(lastNewline + 1).trim();

        if (this._searchTimeout) clearTimeout(this._searchTimeout);

        if (currentLine.length >= 2) {
            this._searchTimeout = setTimeout(() => this._searchNames(currentLine), 300);
        } else {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    async _searchNames(query) {
        try {
            let searchQuery = query.replace(/^(MR\s+|MRS\s+|MS\s+)/i, "").trim();
            if (searchQuery.length < 2) {
                this.state.suggestions = [];
                this.state.showDropdown = false;
                return;
            }
            const results = await this.orm.searchRead(
                "travel.employee.code",
                [["employee_name", "ilike", searchQuery]],
                ["employee_name", "employee_code", "entity", "initial"],
                { limit: 10, order: "employee_name asc" }
            );
            this.state.suggestions = results.filter((r) => r.employee_name);
            this.state.showDropdown = this.state.suggestions.length > 0;
            this.state.selectedIndex = -1;
        } catch {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    onKeydown(ev) {
        if (!this.state.showDropdown) return;
        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.state.selectedIndex = Math.min(
                this.state.selectedIndex + 1,
                this.state.suggestions.length - 1
            );
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            this.state.selectedIndex = Math.max(this.state.selectedIndex - 1, -1);
        } else if (ev.key === "Enter" && this.state.selectedIndex >= 0) {
            ev.preventDefault();
            this.selectSuggestion(this.state.suggestions[this.state.selectedIndex]);
        } else if (ev.key === "Escape") {
            this.state.showDropdown = false;
        }
    }

    selectSuggestion(suggestion) {
        const textarea = this.textareaRef.el;
        const value = textarea ? textarea.value || "" : this.state.value;
        const cursorPos = textarea ? textarea.selectionStart : value.length;
        const beforeCursor = value.substring(0, cursorPos);
        const afterCursor = value.substring(cursorPos);

        const lastNewline = beforeCursor.lastIndexOf("\n");
        const beforeLine = value.substring(0, lastNewline + 1);
        const afterLine = afterCursor.indexOf("\n") >= 0
            ? afterCursor.substring(afterCursor.indexOf("\n"))
            : "";

        const name = suggestion.employee_name.toUpperCase();
        const currentLine = beforeCursor.substring(lastNewline + 1).trim();
        const prefixMatch = currentLine.match(/^(MR\s+|MRS\s+|MS\s+)/i);
        const typedPrefix = prefixMatch ? prefixMatch[0].toUpperCase() : "";
        // Use typed prefix if present, otherwise use initial from employee record
        const prefix = typedPrefix || (suggestion.initial ? suggestion.initial.toUpperCase() + " " : "");

        const newValue = beforeLine + prefix + name + afterLine;
        this.state.value = newValue;
        this.state.showDropdown = false;
        this.state.suggestions = [];
        this.props.record.update({ [this.props.name]: newValue });

        if (textarea) {
            textarea.value = newValue;
        }
    }
}

const passengerAutocomplete = {
    component: PassengerAutocomplete,
    supportedTypes: ["text"],
    extractProps: ({ attrs }) => ({}),
};

registry.category("fields").add("passenger_autocomplete", passengerAutocomplete);

// ─── Char field version (input) for passenger_name ───
class PassengerAutocompleteChar extends Component {
    static template = "travel_booking_management.PassengerAutocompleteChar";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            suggestions: [],
            showDropdown: false,
            selectedIndex: -1,
            value: this.props.record.data[this.props.name] || "",
        });
        this.inputRef = useRef("input");
        this.dropdownRef = useRef("dropdown");
        this._searchTimeout = null;
        this._onDocClick = this._onDocumentClick.bind(this);

        onMounted(() => {
            document.addEventListener("click", this._onDocClick);
            if (this.inputRef.el) {
                this.inputRef.el.value = this.state.value;
            }
        });
        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocClick);
            if (this._searchTimeout) clearTimeout(this._searchTimeout);
        });
        onWillUpdateProps((nextProps) => {
            this.state.value = nextProps.record.data[nextProps.name] || "";
        });
    }

    _onDocumentClick(ev) {
        if (this.dropdownRef.el && !this.dropdownRef.el.contains(ev.target)) {
            this.state.showDropdown = false;
        }
    }

    get isReadonly() {
        return this.props.readonly;
    }

    onInput(ev) {
        const value = ev.target.value;
        this.state.value = value;
        this.props.record.update({ [this.props.name]: value });

        const trimmed = value.trim();
        if (this._searchTimeout) clearTimeout(this._searchTimeout);

        if (trimmed.length >= 2) {
            this._searchTimeout = setTimeout(() => this._searchNames(trimmed), 300);
        } else {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    async _searchNames(query) {
        try {
            let searchQuery = query.replace(/^(MR\s+|MRS\s+|MS\s+)/i, "").trim();
            if (searchQuery.length < 2) {
                this.state.suggestions = [];
                this.state.showDropdown = false;
                return;
            }
            const results = await this.orm.searchRead(
                "travel.employee.code",
                [["employee_name", "ilike", searchQuery]],
                ["employee_name", "employee_code", "entity", "initial"],
                { limit: 10, order: "employee_name asc" }
            );
            this.state.suggestions = results.filter((r) => r.employee_name);
            this.state.showDropdown = this.state.suggestions.length > 0;
            this.state.selectedIndex = -1;
        } catch {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    onKeydown(ev) {
        if (!this.state.showDropdown) return;
        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.state.selectedIndex = Math.min(
                this.state.selectedIndex + 1,
                this.state.suggestions.length - 1
            );
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            this.state.selectedIndex = Math.max(this.state.selectedIndex - 1, -1);
        } else if (ev.key === "Enter" && this.state.selectedIndex >= 0) {
            ev.preventDefault();
            this.selectSuggestion(this.state.suggestions[this.state.selectedIndex]);
        } else if (ev.key === "Escape") {
            this.state.showDropdown = false;
        }
    }

    selectSuggestion(suggestion) {
        const name = suggestion.employee_name.toUpperCase();
        const currentValue = this.state.value.trim();
        const prefixMatch = currentValue.match(/^(MR\s+|MRS\s+|MS\s+)/i);
        const typedPrefix = prefixMatch ? prefixMatch[0].toUpperCase() : "";
        // Use typed prefix if present, otherwise use initial from employee record
        const prefix = typedPrefix || (suggestion.initial ? suggestion.initial.toUpperCase() + " " : "");
        const fullName = prefix + name;
        this.state.value = fullName;
        this.state.showDropdown = false;
        this.state.suggestions = [];
        this.props.record.update({ [this.props.name]: fullName });

        if (this.inputRef.el) {
            this.inputRef.el.value = fullName;
        }
    }
}

const passengerAutocompleteChar = {
    component: PassengerAutocompleteChar,
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({}),
};

registry.category("fields").add("passenger_autocomplete_char", passengerAutocompleteChar);
