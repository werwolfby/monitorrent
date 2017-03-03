<template>
    <div>
        <md-dialog ref="deleteTopicDialog">
            <md-dialog-title>Are you sure?</md-dialog-title>

            <md-dialog-content>Are you sure you want to delete this topic?</md-dialog-content>

            <md-dialog-actions>
                <md-button class="md-primary" @click.native="deleteTopicDialogCancel" ref="deleteTopicDialogNo">No</md-button>
                <md-button class="md-primary md-warn" @click.native="deleteTopicDialogOk" ref="deleteTopicDialogYes">Yes</md-button>
            </md-dialog-actions>
        </md-dialog>

        <mt-topics-execute ref="execute" :loading="loading" :execute="last_execute" :trackers="trackers"></mt-topics-execute>
        <mt-topics-header ref="header" :filter="filter" :order="order" @change-filter="setFilter" @change-order="setOrder" @add-topic="addTopic"></mt-topics-header>
        <mt-topics-list ref="list" :topics="topics" :loading="loading" :canExecuteTracker="canExecuteTracker"
                        @set-paused="setPaused" @reset-status="resetTopicStatus" @delete-topic="deleteTopic">
        </mt-topics-list>
    </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'
import TopicsExecute from './TopicsExecute'
import types from '../../store/types'
import { mapGetters, mapState, mapActions } from 'vuex'

export default {
    name: 'Topics',
    computed: {
        ...mapGetters({
            topics: 'filteredTopics',
            trackers: 'trackers'
        }),
        ...mapState({
            loading: state => state.topics.loading,
            last_execute: state => state.topics.last_execute,
            filter: state => state.topics.filterString,
            order: state => state.topics.order
        })
    },
    components: {
        'mt-topics-list': TopicsList,
        'mt-topics-header': TopicsHeader,
        'mt-topics-execute': TopicsExecute
    },
    created () {
        this.$store.dispatch('loadTopics')
    },
    methods: {
        setFilter (value) {
            this.$store.commit(types.SET_FILTER_STRING, { value })
        },
        setOrder (order) {
            this.$store.commit(types.SET_ORDER, { order })
        },
        canExecuteTracker (tracker) {
            return this.$store.state.topics.topics.some(t => t.tracker === tracker && !t.paused)
        },
        deleteTopic (id) {
            this.$refs.deleteTopicDialog.open()
            this.deleteTopicId = id
        },
        deleteTopicDialogCancel (type) {
            this.$refs.deleteTopicDialog.close()
            this.deleteTopicId = null
        },
        deleteTopicDialogOk (type) {
            this.$refs.deleteTopicDialog.close()
            this.$store.dispatch('deleteTopic', this.deleteTopicId)
            this.deleteTopicId = null
        },
        addTopic () {
        },
        ...mapActions({
            'setPaused': 'setTopicPaused',
            'resetTopicStatus': 'resetTopicStatus'
        })
    }
}
</script>
