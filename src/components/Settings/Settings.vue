<template>
    <div>
        <mt-route-toolbar title="Settings"></mt-route-toolbar>
        <md-divider></md-divider>
        <md-list ref="list" style="padding: 0px">
            <md-list-item v-for="r of routes">
                <router-link :to="r.href">
                    <md-icon>{{r.icon}}</md-icon>
                    <span>{{r.label}}</span>
                </router-link>
            </md-list-item>
        </md-list>
    </div>
</template>

<script>
import RouteToolbar from './RouteToolbar'

export default {
    data: () => ({
        routes: [
            { href: '/settings/general', label: 'General', icon: 'code' },
            { href: '/settings/trackers', label: 'Trackers', icon: 'settings_input_component' },
            { href: '/settings/notifiers', label: 'Notifiers', icon: 'notifications' },
            { href: '/settings/clients', label: 'Clients', icon: 'dns' },
            { href: '/settings/authentication', label: 'Authentication', icon: 'security' },
            { href: '/execute', label: 'Execute', icon: 'input', dev: true },
            { href: '/logs', label: 'Logs', icon: 'format_align_left', dev: true },
            { href: '/about', label: 'About', icon: 'group' }
        ]
    }),
    components: {
        'mt-route-toolbar': RouteToolbar
    },
    name: 'Settings'
}
</script>

<style>
</style>
