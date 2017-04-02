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
                    <md-input v-model="settings.updateInterval" type="number"></md-input>
                    <div class="mt-input-postfix">minutes</div>
                </md-input-container>
            </md-layout>
            <md-divider></md-divider>
            <md-layout md-flex="100" class="mt-padding">
                <md-switch v-model="settings.proxy.enabled" name="enable-proxy" class="md-primary">Enable Proxy</md-switch>
            </md-layout>
            <md-layout v-if="settings.proxy.enabled" md-flex="100" class="mt-padding">
                <md-input-container>
                    <label>Proxy Server for http requests</label>
                    <md-input v-model="settings.proxy.http" placeholder="http://login:password@host:port"></md-input>
                </md-input-container>
            </md-layout>
            <md-layout v-if="settings.proxy.enabled" md-flex="100" class="mt-padding">
                <md-input-container>
                    <label>Proxy Server for https requests</label>
                    <md-input v-model="settings.proxy.https" placeholder="https://login:password@host:port"></md-input>
                </md-input-container>
            </md-layout>
            <md-divider></md-divider>
            <md-layout md-flex="100" class="mt-padding">
                <md-switch v-model="settings.newVersionCheck.enabled" name="enable-proxy" class="md-primary">Check for New Version</md-switch>
            </md-layout>
            <md-layout v-if="settings.newVersionCheck.enabled" md-flex="100" class="mt-padding">
                <md-layout md-flex="50">
                    <md-checkbox v-model="settings.newVersionCheck.preRelease" style="margin: auto 0px" class="md-primary">Check for pre-release versions</md-checkbox>
                </md-layout>
                <md-layout md-flex="50">
                    <md-input-container>
                        <label>Interval</label>
                        <md-input v-model="settings.newVersionCheck.interval" type="number"></md-input>
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
        changeValue () {
            this.$emit('value', {...this.value})
        },
        ...mapActions({
            'loadSettings': 'loadSettings'
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
