<template>
    <div>
        <mt-route-toolbar title="General"></mt-route-toolbar>
        <md-divider></md-divider>
        <md-layout class="mt-padding">
            <md-input-container>
                <label>Torrent Update Interval</label>
                <md-input v-model="updateInterval" type="number"></md-input>
                <div class="mt-input-postfix">minutes</div>
            </md-input-container>
        </md-layout>
        <md-divider></md-divider>
        <md-layout md-flex="100" class="mt-padding">
            <md-switch v-model="proxy.enabled" name="enable-proxy" class="md-primary">Enable Proxy</md-switch>
        </md-layout>
        <md-layout v-if="proxy.enabled" md-flex="100" class="mt-padding">
            <md-input-container>
                <label>Proxy Server for http requests</label>
                <md-input v-model="proxy.http" placeholder="http://login:password@host:port"></md-input>
            </md-input-container>
        </md-layout>
        <md-layout v-if="proxy.enabled" md-flex="100" class="mt-padding">
            <md-input-container>
                <label>Proxy Server for https requests</label>
                <md-input v-model="proxy.https" placeholder="https://login:password@host:port"></md-input>
            </md-input-container>
        </md-layout>
        <md-divider></md-divider>
        <md-layout md-flex="100" class="mt-padding">
            <md-switch v-model="newVersionCheck.enabled" name="enable-proxy" class="md-primary">Check for New Version</md-switch>
        </md-layout>
        <md-layout v-if="newVersionCheck.enabled" md-flex="100" class="mt-padding">
            <md-layout md-flex="50">
                <md-checkbox v-model="newVersionCheck.preRelease" style="margin: auto 0px" class="md-primary">Check for pre-release versions</md-checkbox>
            </md-layout>
            <md-layout md-flex="50">
                <md-input-container>
                    <label>Interval</label>
                    <md-input v-model="newVersionCheck.interval" type="number"></md-input>
                    <div class="mt-input-postfix">minutes</div>
                </md-input-container>
            </md-layout>
        </md-layout>
    </div>
</template>

<script>
import RouteToolbar from './RouteToolbar'

export default {
    data: () => ({
        updateInterval: 15,
        proxy: {
            enabled: false,
            http: null,
            https: null
        },
        newVersionCheck: {
            enabled: false,
            preRelease: true,
            interval: 60
        }
    }),
    components: {
        'mt-route-toolbar': RouteToolbar
    },
    name: 'SettingsGeneral'
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

.mt-input-postfix:after {
    padding: 0px 10px;
}
</style>
