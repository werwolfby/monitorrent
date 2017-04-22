<template>
    <md-dialog ref="addTopicDialog">
        <md-dialog-title ref="title" class="mt-dialog-title">{{isAddMode ? 'Add Topic' : 'Edit Topic'}}</md-dialog-title>

        <md-dialog-content style="width: 500px">
            <!-- Topic URL -->
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container :class="{'md-input-invalid': !topic.loading && topic.error}">
                        <label>URL</label>
                        <md-input ref="topicUrlInput" v-model="topic.url" :disabled="isEditMode"></md-input>
                        <span ref="topicError" v-if="!topic.loading && topic.error" class="md-error">{{topic.error}}</span>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress ref="topicProgress" md-indeterminate :style="{opacity: topic.loading ? 1 : 0}"></md-progress>
            <!-- Topic Settings -->
            <mt-dynamic-form ref="dynamicForm" :form="topic.form"></mt-dynamic-form>

            <!-- Additional fields -->
            <!-- Download Dir -->
            <md-layout md-gutter="24">
                <md-layout md-flex="100">
                    <md-input-container :class="{'md-input-invalid': !additionalFields.downloadDir.loading && !additionalFields.downloadDir.support}">
                        <label>Download dir</label>
                        <md-input ref="downloadDirInput" v-model="additionalFields.downloadDir.path" :disabled="additionalFields.downloadDir.loading || !additionalFields.downloadDir.support"></md-input>
                        <span ref="downloadDirNotSupportedError" v-if="!additionalFields.downloadDir.loading && additionalFields.downloadDir.complete && !additionalFields.downloadDir.support" class="md-error">
                            {{additionalFields.downloadDir.defaultClientName}} doesn't support download dir settings
                        </span>
                        <span ref="downloadDirError" v-else-if="!additionalFields.downloadDir.loading && additionalFields.downloadDir.error" class="md-error">
                            {{additionalFields.downloadDir.error}}
                        </span>
                    </md-input-container>
                </md-layout>
            </md-layout>
            <md-progress ref="downloadDirProgress" md-indeterminate :style="{opacity: additionalFields.downloadDir.loading ? 1 : 0}"></md-progress>
        </md-dialog-content>

        <md-dialog-actions>
            <md-button class="md-primary" ref="addTopicDialogCancel" @click.native="close">Cancel</md-button>
            <md-button v-if="isAddMode" class="md-primary md-accent" ref="add" :disabled="loading || !complete" @click.native="addEdit">Add</md-button>
            <md-button v-if="isEditMode" class="md-primary md-accent" ref="save" :disabled="loading || !complete" @click.native="addEdit">Save</md-button>
        </md-dialog-actions>
    </md-dialog>
</template>

<script>
import api from '../../api/monitorrent'
import DynamicForm from '../DynamicForm'

export default {
    data: () => ({
        mode: 'add',
        topic: {
            id: 0,
            loading: false,
            url: '',
            form: {},
            parsed: false,
            error: null
        },
        additionalFields: {
            downloadDir: {
                complete: false,
                defaultClientName: null,
                loading: false,
                support: false,
                path: '',
                originalPath: '',
                error: null
            }
        }
    }),
    computed: {
        loading () {
            return this.topic.loading || this.additionalFields.downloadDir.loading
        },
        complete () {
            return this.topic.parsed && this.additionalFields.downloadDir.complete
        },
        isAddMode () {
            return this.mode === 'add'
        },
        isEditMode () {
            return this.mode === 'edit'
        }
    },
    watch: {
        'topic.url' () {
            if (this.isAddMode) {
                this.parseUrl()
            }
        }
    },
    name: 'AddTopicDialog',
    components: {
        'mt-dynamic-form': DynamicForm
    },
    methods: {
        async parseUrl () {
            this.topic.error = null

            if (!this.topic.url) {
                this.topic.form = {rows: []}
                return
            }

            try {
                this.topic.loading = true
                this.topic.parsed = false

                const parseResult = await api.topics.parseUrl(this.topic.url)

                this.topic.error = null
                this.topic.form = {rows: parseResult.form, model: parseResult.settings}
                this.topic.parsed = true
            } catch (err) {
                this.topic.form = {rows: []}
                if (err.message === 'CantParse') {
                    this.topic.error = err.description
                } else {
                    this.topic.error = err.toString()
                    console.error(err)
                }
            } finally {
                this.topic.loading = false
            }
        },
        async loadTopic (id) {
            try {
                this.topic.loading = true
                this.topic.parsed = false

                const topic = await api.topics.get(id)

                this.topic.error = null
                this.topic.url = topic.settings.url
                this.topic.form = {rows: topic.form, model: topic.settings}
                this.topic.parsed = true

                await this.defaultClient()

                this.additionalFields.downloadDir.path = topic.settings.download_dir
            } catch (err) {
                this.topic.error = err.toString()
                console.error(err)
            } finally {
                this.topic.loading = false
            }
        },
        async defaultClient () {
            try {
                this.additionalFields.downloadDir.complete = false
                this.additionalFields.downloadDir.path = ''
                this.additionalFields.downloadDir.support = false
                this.additionalFields.downloadDir.defaultClientName = ''
                this.additionalFields.downloadDir.loading = true

                const defaultClient = await api.defaultClient()
                const downloadDir = defaultClient.fields.download_dir

                this.additionalFields.downloadDir.complete = true
                this.additionalFields.downloadDir.path = downloadDir || ''
                this.additionalFields.downloadDir.originalPath = downloadDir || ''
                this.additionalFields.downloadDir.support = downloadDir !== null && downloadDir !== undefined
                this.additionalFields.downloadDir.defaultClientName = defaultClient.name
            } catch (err) {
                this.additionalFields.downloadDir.error = err.toString()
                console.error(err)
            } finally {
                this.additionalFields.downloadDir.loading = false
            }
        },
        open () {
            this.mode = 'add'
            this.topic.id = 0
            this.topic.url = null
            this.$refs.addTopicDialog.open()
            return this.defaultClient()
        },
        openEdit (id) {
            this.mode = 'edit'
            this.topic.id = id
            this.topic.url = null
            this.$refs.addTopicDialog.open()
            return this.loadTopic(id)
        },
        close () {
            this.$refs.addTopicDialog.close()
        },
        addEdit () {
            const downloadDirChanged = this.additionalFields.downloadDir.support &&
                (this.additionalFields.downloadDir.originalPath !== this.additionalFields.downloadDir.path)
            const downloadDir = downloadDirChanged ? this.additionalFields.downloadDir.path : null

            const additionalFields = {
                download_dir: downloadDir
            }

            const url = this.topic.url
            const settings = {...this.$refs.dynamicForm.model, ...additionalFields}

            if (this.isEditMode) {
                this.$emit('edit-topic', {id: this.topic.id, settings})
            } else {
                this.$emit('add-topic', {url, settings})
            }
        }
    }
}
</script>

<style scoped>
.mt-dialog-title {
    background-color: #607d8b;
    padding-bottom: 20px;
    color: white
}
</style>
