<template>
    <div>
        <mt-route-toolbar :title="tracker"></mt-route-toolbar>
        <md-divider></md-divider>
        <div v-if="loading">
            <div ref="loading">Loading...</div>
        </div>
        <div v-else>
            <div class='dynamic-container'>
                <mt-dynamic-form v-if="trackerForm" ref="dynamicForm" :form="trackerForm" @changed="formChanged" @focused="formFocused"></mt-dynamic-form>
                <div v-else>There are no settings for this tracker</div>
            </div>
            <md-divider v-if="trackerForm"></md-divider>
            <div v-if="trackerForm" class='button-container'>
                <md-button class="md-raised md-primary" :disabled="!canSave">Save</md-button>
                <md-button class="md-raised md-primary md-accent" :disabled="!canCheck" v-if="showCheck">Check</md-button>
            </div>
        </div>
    </div>
</template>

<script>
import DynamicForm from '../DynamicForm'
import RouteToolbar from './RouteToolbar'
import { mapActions, mapState } from 'vuex'

export default {
    props: {
        tracker: {
            type: String,
            required: true
        }
    },
    data: function () {
        return {
            rows: null,
            model: null,
            canSave: false,
            canCheck: false,
            showCheck: true
        }
    },
    computed: {
        trackerForm () {
            const rows = this.rows
            const model = this.model
            return rows ? { rows, model } : null
        },
        ...mapState({
            trackers: state => state.trackers.trackers,
            loading: state => state.trackers.loading
        })
    },
    watch: {
        trackers () {
            const trackerObj = this.trackers ? this.trackers.find(t => t.name === this.tracker) : undefined
            this.rows = trackerObj ? trackerObj.form : null
            let passwords = null
            if (this.rows && trackerObj.model) {
                const passwordElements = this.rows
                    .reduce((a, b) => a.concat(b.content), [])
                    .filter(e => e.type === 'password')
                passwords = passwordElements.reduce((a, e) => ({...a, [e.model]: '******'}), {})
                this.clearedPasswords = passwordElements.reduce((a, e) => ({...a, [e.model]: ''}), {})
            }
            // fake all passwords fields from backend side
            this.model = passwords ? {...trackerObj.model, ...passwords} : {}
            this.showCheck = trackerObj ? trackerObj.canCheck : false
            this.canCheck = !!passwords
        }
    },
    components: {
        'mt-route-toolbar': RouteToolbar,
        'mt-dynamic-form': DynamicForm
    },
    name: 'SettingsTracker',
    created () {
        this.loadTracker(this.tracker)
    },
    methods: {
        formChanged ({ model, value }) {
            if (!this.model || (this.model[model] === value)) {
                return
            }

            this.canSave = true
            // Clear all fake password on first change
            if (this.clearedPasswords) {
                this.model = {...this.model, [model]: value, ...this.clearedPasswords}
                this.clearedPasswords = null
            }
        },
        formFocused ({ model }) {
            // Clear all fake password on first focus of password field if it wasn't cleared yet
            if (this.clearedPasswords && this.clearedPasswords.hasOwnProperty(model)) {
                this.model = {...this.model, ...this.clearedPasswords}
                this.clearedPasswords = null
            }
        },
        ...mapActions({
            'loadTracker': 'loadTracker'
        })
    }
}
</script>

<style scoped>
.dynamic-container {
    padding: 20px;
}

.button-container {
    display: flex;
    justify-content: flex-end;
}
</style>
