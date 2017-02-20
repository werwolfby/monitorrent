import moment from 'moment'

export function formatDate (value, format) {
    if (value) {
        return moment(value).format(format || 'DD.MM.YYYY HH:mm:ss')
    }

    return ''
}

export function isNull (value, nullValue) {
    return value || nullValue
}
