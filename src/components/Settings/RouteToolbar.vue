<template>
    <md-layout>
        <md-button class="md-icon-button" style="margin: auto 12px" @click.native="$router.back()">
            <md-icon>arrow_back</md-icon>
        </md-button>
        <h2>{{title}}</h2>
    </md-layout>
</template>

<script>
export default {
    props: {
        'title': {
            type: String,
            required: true
        }
    },
    name: 'RouteToolbar'
}
</script>
