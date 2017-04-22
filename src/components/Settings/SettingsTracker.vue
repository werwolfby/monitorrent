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
                <div v-else>There are no settigs for this tracker</div>
            </div>
            <md-divider v-if="trackerForm"></md-divider>
            <div v-if="trackerForm" class='button-container'>
                <md-button class="md-raised md-primary" :disabled="!canSave">Save</md-button>
                <md-button class="md-raised md-primary md-accent" :disabled="!canCheck">Check</md-button>
            </div>
        </div>
    </div>
</template>

<script>
import DynamicForm from '../DynamicForm'
import RouteToolbar from './RouteToolbar'
import { mapActions, mapState } from 'vuex'

const emptyArray = []

function findPasswords (rows) {
    if (!rows || rows.length === 0) {
        return emptyArray
    }

    return rows
        .reduce((a, b) => a.concat(b.content), [])
        .filter(e => e.type === 'password')
        .reduce((a, e) => ({...a, [e.model]: '******'}), {})
}

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
            canCheck: false
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
            this.passwords = findPasswords(this.rows)
            this.dirtyPassword = Object.keys(this.passwords).reduce((a, p) => ({...a, [p]: false}), {})
            this.model = trackerObj && trackerObj.model && Object.keys(trackerObj.model).length > 0
                ? {...trackerObj.model, ...this.passwords}
                : {}
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
            this.canSave = true
            // If password was changed, make it dirty (changed)
            if (this.passwords.hasOwnProperty(model)) {
                this.dirtyPassword[model] = true
            }

            // Reset all other not dirty password
            let clearedPasswords = null
            for (const password of Object.keys(this.passwords)) {
                if (!this.dirtyPassword[password]) {
                    if (clearedPasswords === null) clearedPasswords = {}
                    clearedPasswords[password] = ''
                }
            }
            // if we still have any not edited password field then clear it,
            // and don't forget to update changed model ([model]: value)
            if (clearedPasswords) {
                this.model = {...this.model, [model]: value, ...clearedPasswords}
            }
        },
        formFocused ({ model }) {
            // Clear password that wasn't edited yet on password field focus
            if (this.passwords.hasOwnProperty(model) && !this.dirtyPassword[model]) {
                this.model = {...this.model, [model]: ''}
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
