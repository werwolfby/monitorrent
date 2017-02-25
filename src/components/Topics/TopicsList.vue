<template>
  <div>
    <div v-if="loading">
        <md-layout ref="loading" md-align="center" md-gutter="16">
            <span>Loading...</span>
        </md-layout>
    </div>
    <template v-else>
        <md-list ref="list" class="md-double-line" style="padding: 0px" v-if="topics && topics.length > 0">
            <md-list-item ref="topic" v-for="topic in topics" :class="[topic.paused ? 'mt-color-paused' : '', !topic.paused && topic.status != 'Ok' ? 'mt-color-failed' : '']">
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
                        <md-menu-item ref="menuItem">
                            <md-icon>edit</md-icon><span>Edit</span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem" v-if="!topic.paused">
                            <md-icon>pause</md-icon><span>Pause</span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem" v-else>
                            <md-icon>play_circle_outline</md-icon><span>Unpause</span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem" v-if="topic.status != 'Ok' && !topic.paused">
                            <md-icon>restore</md-icon><span>Reset Status</span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem" v-if="!topic.paused">
                            <md-icon>input</md-icon><span>Execute</span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem" v-if="canExecuteTracker(topic.tracker)">
                            <md-icon>input</md-icon><span>Execute <b>{{topic.tracker}}</b></span>
                        </md-menu-item>
                        <md-menu-item ref="menuItem">
                            <md-icon>delete</md-icon><span>Delete</span>
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
        },
        'canExecuteTracker': {
            type: Function,
            default: () => true
        }
    },
    name: 'TopicsList'
}
</script>

<style>
.mt-color-failed {
    background-color: #FFCDD2;
}

.mt-color-warn {
    background-color: #FFE0B2;
}

.mt-color-paused {
    background-color: #DCEDC8;
}

.mt-color-downloaded {
    background-color: #C8E6C9;
}
</style>
