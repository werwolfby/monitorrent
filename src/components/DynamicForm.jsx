function renderText (h, data, state, events) {
    const onInput = (value) => {
        state.model[data.model] = value
        events.changed(data.model, value)
    }

    const onFocus = () => {
        events.focused(data.model)
    }

    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-input ref={`input-${data.model}`} type={data.type} value={state.model[data.model]} onInput={onInput} nativeOnFocus={onFocus}></md-input>
            </md-input-container>
        </md-layout>)
}

function renderSelect (h, data, state, events) {
    const onInput = (value) => {
        state.model[data.model] = value
        events.changed(data.model, value)
    }

    return (<md-layout md-flex={data.flex} ref={data.model}>
            <md-input-container>
                <label>{data.label}</label>
                <md-select ref={`input-${data.model}`} value={state.model[data.model]} onInput={onInput}>
                    {data.options.map(o => (<md-option value={o}>{o}</md-option>))}
                </md-select>
            </md-input-container>
        </md-layout>)
}

function renderRow (h, data, state, events) {
    const ref = `row${state.row++}`
    return (<md-layout md-gutter={state.gutter} ref={ref}>
            {data.content.map(c => renderContent(h, c, state, events))}
        </md-layout>)
}

const contentFactory = {
    'row': renderRow,
    'password': renderText,
    'text': renderText,
    'number': renderText,
    'select': renderSelect
}

function renderContent (h, data, state, events) {
    const factory = contentFactory[data.type]
    if (factory) {
        return factory(h, data, state, events)
    }
}

export default {
    name: 'mtDynamicForm',
    props: {
        'form': {
            type: Object,
            default: () => ({
                rows: [],
                model: {}
            })
        },
        'gutter': {
            type: Number,
            default: 24
        }
    },
    watch: {
        form (newForm) {
            this.updateForm(newForm)
        }
    },
    data: () => ({
        model: {}
    }),
    methods: {
        updateForm (form) {
            const newModel = {}
            const rows = form.rows || []
            const model = form.model || {}
            for (let row of rows) {
                for (let content of row.content) {
                    newModel[content.model] = model[content.model] || null
                }
            }
            this.$set(this, 'model', newModel)
        },
        changed (model, value) {
            this.$emit('changed', { model, value })
        },
        focused (model) {
            this.$emit('focused', { model })
        }
    },
    created () {
        this.updateForm(this.form)
    },
    render (h) {
        const state = {row: 0, gutter: this.gutter, model: this.model}
        const events = {changed: this.changed, focused: this.focused}
        const rows = this.form.rows || []
        return (<form autocomplete="off">
                {rows.map(r => renderContent(h, r, state, events))}
            </form>)
    }
}
