<template>
    <div>
        <mt-route-toolbar :title="tracker"></mt-route-toolbar>
        <md-divider></md-divider>
        <div v-if="loading">
            <div ref="loading">Loading...</div>
        </div>
        <div v-else>
            <div class='dynamic-container'>
                <mt-dynamic-form v-if="trackerForm" ref="dynamicForm" :form="trackerForm"></mt-dynamic-form>
                <div v-else>There are no settigs for this tracker</div>
            </div>
            <md-divider v-if="trackerForm"></md-divider>
            <div v-if="trackerForm" class='button-container'>
                <md-button class="md-raised md-primary">Save</md-button>
                <md-button class="md-raised md-primary md-accent">Check</md-button>
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
        }
    },
    computed: {
        ...mapState({
            trackers: state => state.trackers.trackers,
            loading: state => state.trackers.loading
        }),
        trackerForm: function () {
            const trackerObj = this.trackers ? this.trackers.find(t => t.name === this.tracker) : undefined
            const rows = trackerObj ? trackerObj.form : null
            const model = trackerObj ? {...trackerObj.model, password: '******'} : {}
            return rows ? { rows, model } : null
        }
    },
    components: {
        'mt-route-toolbar': RouteToolbar,
        'mt-dynamic-form': DynamicForm
    },
    name: 'SettingsTracker',
    async created () {
        this.loadTracker(this.tracker)
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
</style>
