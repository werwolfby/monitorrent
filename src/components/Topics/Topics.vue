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

        <mt-add-topic-dialog ref="addEditTopicDialog" @add-topic="addTopicHandler" @edit-topic="editTopicHandler">
        </mt-add-topic-dialog>

        <mt-topics-execute ref="execute" :loading="executeLoading" :execute="lastExecute" :trackers="trackers"
                           :executing="executing" :executingLogs="executingLogs"
                           @execute="executeAll" @execute-tracker="executeTracker">
        </mt-topics-execute>
        <mt-topics-header ref="header" :filter="filter" :order="order" @change-filter="setFilter" @change-order="setOrder" @add-topic="addTopicClicked"></mt-topics-header>
        <mt-topics-list ref="list" :topics="topics" :loading="topicsLoading" :canExecuteTracker="canExecuteTracker"
                        @edit-topic="editTopicClicked" @set-paused="setPaused" @reset-status="resetTopicStatus" @delete-topic="deleteTopicHandler"
                        @execute="execute" @execute-tracker="executeTracker">
        </mt-topics-list>
    </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'
import TopicsExecute from './TopicsExecute'
import AddTopicDialog from './AddTopicDialog'
import api from '../../api/monitorrent'
import { mapGetters, mapState, mapActions } from 'vuex'

export default {
    name: 'Topics',
    data: () => ({
        addEditTopicMode: 'add'
    }),
    computed: {
        ...mapGetters({
            topics: 'filteredTopics',
            trackers: 'trackers'
        }),
        ...mapState({
            topicsLoading: state => state.topics.loading,
            filter: state => state.topics.filterString,
            order: state => state.topics.order
        }),
        ...mapState({
            executeLoading: state => state.execute.loading,
            lastExecute: state => state.execute.lastExecute,
            executing: state => state.execute.executing,
            executingLogs: state => state.execute.currentExecuteLogs
        })
    },
    components: {
        'mt-topics-list': TopicsList,
        'mt-topics-header': TopicsHeader,
        'mt-topics-execute': TopicsExecute,
        'mt-add-topic-dialog': AddTopicDialog
    },
    created () {
        this.$store.dispatch('loadTopics')
        this.$store.dispatch('loadLastExecute')
        this.watchExecute = this.$store.dispatch('watchExecute')
    },
    methods: {
        canExecuteTracker (tracker) {
            return this.$store.state.topics.topics.some(t => t.tracker === tracker && !t.paused)
        },
        deleteTopicHandler (id) {
            this.$refs.deleteTopicDialog.open()
            this.deleteTopicId = id
        },
        deleteTopicDialogCancel (type) {
            this.$refs.deleteTopicDialog.close()
            this.deleteTopicId = null
        },
        deleteTopicDialogOk (type) {
            this.$refs.deleteTopicDialog.close()
            this.deleteTopic(this.deleteTopicId)
            this.deleteTopicId = null
        },
        addTopicClicked () {
            this.$refs.addEditTopicDialog.open()
        },
        async addTopicHandler (model) {
            await this.addTopic(model)
            this.$refs.addEditTopicDialog.close()
        },
        async editTopicHandler (model) {
            await this.editTopic(model)
            this.$refs.addEditTopicDialog.close()
        },
        async editTopicClicked (id) {
            await this.$refs.addEditTopicDialog.openEdit(id)
        },
        async executeAll () {
            await api.execute.execute(null)
        },
        async execute (id) {
            await api.execute.execute([id])
        },
        async executeTracker (tracker) {
            await api.execute.executeTracker(tracker)
        },
        ...mapActions({
            'setFilter': 'setFilter',
            'setOrder': 'setOrder',
            'setPaused': 'setTopicPaused',
            'resetTopicStatus': 'resetTopicStatus',
            'addTopic': 'addTopic',
            'editTopic': 'editTopic',
            'deleteTopic': 'deleteTopic'
        })
    }
}
</script>
