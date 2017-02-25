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

                <md-menu ref="menu" class="md-list-action" md-direction="bottom left" md-size="4">
                    <md-button md-menu-trigger class="md-icon-button">
                        <md-icon>more_vert</md-icon>
                    </md-button>
                    <md-menu-content ref="menuContent" md-size="4">
                        <md-menu-item @selected="editTopic(topic.id)">
                            <md-icon>edit</md-icon><span>Edit</span>
                        </md-menu-item>
                        <md-menu-item v-if="!topic.paused" @selected="setPaused(topic.id, true)">
                            <md-icon>pause</md-icon><span>Pause</span>
                        </md-menu-item>
                        <md-menu-item v-else @selected="setPaused(topic.id, false)">
                            <md-icon>play_circle_outline</md-icon><span>Unpause</span>
                        </md-menu-item>
                        <md-menu-item v-if="topic.status != 'Ok' && !topic.paused" @selected="resetStatus(topic.id)">
                            <md-icon>restore</md-icon><span>Reset Status</span>
                        </md-menu-item>
                        <md-menu-item v-if="!topic.paused" @selected="execute(topic.id)">
                            <md-icon>input</md-icon><span>Execute</span>
                        </md-menu-item>
                        <md-menu-item v-if="canExecuteTracker(topic.tracker)" @selected="executeTracker(topic.tracker)">
                            <md-icon>input</md-icon><span>Execute <b>{{topic.tracker}}</b></span>
                        </md-menu-item>
                        <md-menu-item class="md-warn" @selected="deleteTopic(topic.id)">
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
    name: 'TopicsList',
    methods: {
        editTopic (id) {
            this.$emit('edit-topic', id)
        },
        setPaused (id, value) {
            this.$emit('set-paused', { id, value })
        },
        resetStatus (id) {
            this.$emit('reset-status', id)
        },
        execute (id) {
            this.$emit('execute', id)
        },
        executeTracker (tracker) {
            this.$emit('execute-tracker', tracker)
        },
        deleteTopic (id) {
            this.$emit('delete-topic', id)
        }
    }
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
