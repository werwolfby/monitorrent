<template>
    <div>
        <mt-route-toolbar :title="tracker"></mt-route-toolbar>
        <md-divider></md-divider>
        <div v-if="loading">
            <div ref="loading">Loading...</div>
        </div>
        <div v-else>
            <div class='dynamic-container'>
                <mt-dynamic-form ref="dynamicForm" :form="trackerForm"></mt-dynamic-form>
            </div>
            <md-divider></md-divider>
            <div class='button-container'>
                <md-button class="md-raised md-primary">Save</md-button>
                <md-button class="md-raised md-primary md-accent">Check</md-button>
            </div>
        </div>
    </div>
</template>

<script>
import DynamicForm from '../DynamicForm.jsx'
import RouteToolbar from './RouteToolbar'
import { mapActions, mapState } from 'vuex'

export default {
    props: {
        tracker: String
    },
    data: function () {
        return {
            loading: true
        }
    },
    computed: {
        ...mapState({
            trackers: state => state.trackers.trackers
        }),
        trackerForm: function () {
            const trackerObj = this.trackers ? this.trackers.find(t => t.name === this.tracker) : undefined
            return { rows: trackerObj ? trackerObj.form : [], model: trackerObj ? trackerObj.model : {} }
        }
    },
    components: {
        'mt-route-toolbar': RouteToolbar,
        'mt-dynamic-form': DynamicForm
    },
    name: 'SettingsTracker',
    async created () {
        await this.loadTracker(this.tracker)
        this.loading = false
    },
    methods: {
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

.md-select {
    min-width: 64px !important;
}
</style>
