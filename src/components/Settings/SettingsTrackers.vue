<template>
    <div>
        <mt-route-toolbar title="Trackers"></mt-route-toolbar>
        <md-divider></md-divider>
        <md-list ref="list" style="padding: 0px">
            <md-list-item v-for="t of trackers">
                <md-avatar>
                    <img :src="`static/images/${t.name}.png`" :alt="t.name">
                </md-avatar>
                <span>{{t.name}}</span>
            </md-list-item>
        </md-list>
    </div>
</template>

<script>
import RouteToolbar from './RouteToolbar'
import { mapActions, mapState } from 'vuex'
import _ from 'lodash'

export default {
    computed: {
        ...mapState({
            loading: state => state.trackers.loading,
            trackers: state => _.sortBy(state.trackers.trackers, 'name')
        })
    },
    components: {
        'mt-route-toolbar': RouteToolbar
    },
    name: 'SettingsTrackers',
    created () {
        this.loadTrackers()
    },
    methods: {
        ...mapActions({
            loadTrackers: 'loadTrackers'
        })
    }
}
</script>
