<template>
    <div>
        <mt-route-toolbar :title="tracker"></mt-route-toolbar>
    </div>
</template>

<script>
import RouteToolbar from './RouteToolbar'

export default {
    props: {
        tracker: String
    },
    components: {
        'mt-route-toolbar': RouteToolbar
    },
    name: 'SettingsTracker'
}
</script>
