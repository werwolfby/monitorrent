<template>
  <div>
    <div v-if="loading">
        <md-layout ref="loading" md-align="center" md-gutter="16">
            <span>Loading...</span>
        </md-layout>
    </div>
    <template v-else>
        <md-list ref="list" class="md-double-line" style="padding: 0px" v-if="topics && topics.length > 0">
            <md-list-item ref="topic" v-for="topic in topics">
                <md-avatar>
                    <a :href="topic.url" target="_blank" hide-gt-xs>
                        <img v-bind:src="'static/images/' + topic.tracker + '.png'"/>
                    </a>
                </md-avatar>

                <div class="md-list-text-container">
                    <span>{{topic.display_name}}</span>
                    <span>Last update: {{topic.last_update | formatDate('DD.MM.YYYY HH:mm:ss') | isNull('not specified')}}</span>
                </div>

                <md-menu class="md-list-action" md-direction="bottom left" md-size="4">
                    <md-button md-menu-trigger class="md-icon-button">
                        <md-icon>more_vert</md-icon>
                    </md-button>
                    <md-menu-content md-size="4">
                        <md-menu-item>
                            <md-icon>edit</md-icon><span>Edit</span>
                        </md-menu-item>
                        <md-menu-item>
                            <md-icon>pause</md-icon><span>Pause</span>
                        </md-menu-item>
                        <md-menu-item>
                            <md-icon>restore</md-icon><span>Reset Status</span>
                        </md-menu-item>
                        <md-menu-item>
                            <md-icon>input</md-icon><span>Execute</span>
                        </md-menu-item>
                    </md-menu-content>
                </md-menu>
            </md-list-item>
        </md-list>
        <div v-else>
            <md-layout ref="addTopics" md-align="center" md-gutter="16">
                <span>Add torrent and press execute</span>
            </md-layout>
        </div>
    </template>
  </div>
</template>

<script>
export default {
    props: {
        'topics': {
            type: Array,
            default: () => []
        },
        'loading': {
            type: Boolean,
            default: true
        }
    },
    name: 'TopicsList'
}
</script>
