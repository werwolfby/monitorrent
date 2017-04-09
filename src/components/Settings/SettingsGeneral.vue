<template>
    <div>
        <mt-route-toolbar title="General"></mt-route-toolbar>
        <md-divider></md-divider>
        <div v-if="loading">
            <div>Loading...</div>
        </div>
        <div v-else>
            <md-layout class="mt-padding">
                <md-input-container>
                    <label>Torrent Update Interval</label>
                    <md-input :value="settings.updateInterval" @input="setUpdateInterval" type="number"></md-input>
                    <div class="mt-input-postfix">minutes</div>
                </md-input-container>
            </md-layout>
            <md-divider></md-divider>
            <md-layout md-flex="100" class="mt-padding">
                <md-switch :value="settings.proxy.enabled" @input="setProxyEnabled" name="enable-proxy" class="md-primary">Enable Proxy</md-switch>
            </md-layout>
            <md-layout v-if="settings.proxy.enabled" md-flex="100" class="mt-padding">
                <md-input-container>
                    <label>Proxy Server for http requests</label>
                    <md-input :value="settings.proxy.http" @input="setProxy({type: 'http', value: $event})" placeholder="http://login:password@host:port"></md-input>
                </md-input-container>
            </md-layout>
            <md-layout v-if="settings.proxy.enabled" md-flex="100" class="mt-padding">
                <md-input-container>
                    <label>Proxy Server for https requests</label>
                    <md-input :value="settings.proxy.https" @input="setProxy({type: 'https', value: $event})" placeholder="https://login:password@host:port"></md-input>
                </md-input-container>
            </md-layout>
            <md-divider></md-divider>
            <md-layout md-flex="100" class="mt-padding">
                <md-switch :value="settings.newVersionCheck.enabled" @input="setNewVersionCheckEnabled" name="enable-proxy" class="md-primary">Check for New Version</md-switch>
            </md-layout>
            <md-layout v-if="settings.newVersionCheck.enabled" md-flex="100" class="mt-padding">
                <md-layout md-flex="50">
                    <md-checkbox :value="settings.newVersionCheck.preRelease" @input="setNewVersionCheckIncludePrerelease" style="margin: auto 0px" class="md-primary">Check for pre-release versions</md-checkbox>
                </md-layout>
                <md-layout md-flex="50">
                    <md-input-container>
                        <label>Interval</label>
                        <md-input :value="settings.newVersionCheck.interval" @input="setNewVersionCheckInterval" type="number"></md-input>
                        <div class="mt-input-postfix">minutes</div>
                    </md-input-container>
                </md-layout>
            </md-layout>
        </div>
    </div>
</template>

<script>
import RouteToolbar from './RouteToolbar'
import { mapActions, mapState } from 'vuex'
import { debounce } from 'lodash'

export default {
    computed: {
        ...mapState({
            loading: state => state.settings.loading,
            settings: state => state.settings.settings
        })
    },
    components: {
        'mt-route-toolbar': RouteToolbar
    },
    name: 'SettingsGeneral',
    created () {
        this.loadSettings()
    },
    methods: {
        setProxy: debounce(function (evt) {
            this.setProxyAction(evt)
        }, 500),
        setUpdateInterval: debounce(function (evt) {
            this.setUpdateIntervalAction(evt)
        }, 500),
        setNewVersionCheckInterval: debounce(function (evt) {
            this.setNewVersionCheckIntervalAction(evt)
        }, 500),
        ...mapActions({
            'loadSettings': 'loadSettings',
            'setProxyEnabled': 'setProxyEnabled',
            'setProxyAction': 'setProxy',
            'setNewVersionCheckEnabled': 'setNewVersionCheckEnabled',
            'setNewVersionCheckIncludePrerelease': 'setNewVersionCheckIncludePrerelease',
            'setNewVersionCheckIntervalAction': 'setNewVersionCheckInterval',
            'setUpdateIntervalAction': 'setUpdateInterval'
        })
    }
}
</script>

<style scoped>
.mt-padding {
    padding: 0px 16px;
}

.mt-input-postfix {
    margin: auto;
    padding: 0px 10px;
}
</style>
