#include "oscope/reporting/json_value.hpp"

#include <cstdio>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace oscope::reporting {

std::string escape_json_string(std::string_view input) {
    std::string result;
    result.reserve(input.size() + 8);

    for (unsigned char c : input) {
        switch (c) {
            case '"':
                result += "\\\"";
                break;
            case '\\':
                result += "\\\\";
                break;
            case '\b':
                result += "\\b";
                break;
            case '\f':
                result += "\\f";
                break;
            case '\n':
                result += "\\n";
                break;
            case '\r':
                result += "\\r";
                break;
            case '\t':
                result += "\\t";
                break;
            default:
                if (c < 0x20) {
                    // Control character: format as \u00xx
                    char hex_buf[7];
                    std::snprintf(hex_buf, sizeof(hex_buf), "\\u%04X", static_cast<unsigned int>(c));
                    result += hex_buf;
                } else {
                    result += static_cast<char>(c);
                }
                break;
        }
    }

    return result;
}

JsonValue::JsonValue() : storage_(std::monostate{}) {}
JsonValue::JsonValue(std::nullptr_t) : storage_(std::monostate{}) {}
JsonValue::JsonValue(bool val) : storage_(val) {}
JsonValue::JsonValue(int val) : storage_(static_cast<std::int64_t>(val)) {}
JsonValue::JsonValue(long val) : storage_(static_cast<std::int64_t>(val)) {}
JsonValue::JsonValue(long long val) : storage_(static_cast<std::int64_t>(val)) {}
JsonValue::JsonValue(unsigned int val) : storage_(static_cast<std::uint64_t>(val)) {}
JsonValue::JsonValue(unsigned long val) : storage_(static_cast<std::uint64_t>(val)) {}
JsonValue::JsonValue(unsigned long long val) : storage_(static_cast<std::uint64_t>(val)) {}
JsonValue::JsonValue(double val) : storage_(val) {}
JsonValue::JsonValue(const char* val) : storage_(val ? std::string(val) : std::string{}) {}
JsonValue::JsonValue(std::string val) : storage_(std::move(val)) {}
JsonValue::JsonValue(std::string_view val) : storage_(std::string(val)) {}
JsonValue::JsonValue(ArrayType arr) : storage_(std::move(arr)) {}
JsonValue::JsonValue(ObjectType obj) : storage_(std::move(obj)) {}
JsonValue::JsonValue(std::initializer_list<std::pair<std::string, JsonValue>> init_list)
    : storage_(ObjectType(init_list.begin(), init_list.end())) {}

JsonValue JsonValue::null() {
    return JsonValue{};
}

JsonValue JsonValue::boolean(bool val) {
    return JsonValue{val};
}

JsonValue JsonValue::integer(std::int64_t val) {
    return JsonValue{val};
}

JsonValue JsonValue::unsigned_integer(std::uint64_t val) {
    return JsonValue{val};
}

JsonValue JsonValue::number(double val) {
    return JsonValue{val};
}

JsonValue JsonValue::string(std::string_view val) {
    return JsonValue{val};
}

JsonValue JsonValue::array(ArrayType elements) {
    return JsonValue{std::move(elements)};
}

JsonValue JsonValue::object(ObjectType properties) {
    return JsonValue{std::move(properties)};
}

JsonType JsonValue::type() const noexcept {
    switch (storage_.index()) {
        case 0: return JsonType::Null;
        case 1: return JsonType::Boolean;
        case 2: return JsonType::Integer;
        case 3: return JsonType::UnsignedInteger;
        case 4: return JsonType::Number;
        case 5: return JsonType::String;
        case 6: return JsonType::Array;
        case 7: return JsonType::Object;
        default: return JsonType::Null;
    }
}

bool JsonValue::is_null() const noexcept {
    return std::holds_alternative<std::monostate>(storage_);
}

bool JsonValue::is_bool() const noexcept {
    return std::holds_alternative<bool>(storage_);
}

bool JsonValue::is_integer() const noexcept {
    return std::holds_alternative<std::int64_t>(storage_);
}

bool JsonValue::is_unsigned_integer() const noexcept {
    return std::holds_alternative<std::uint64_t>(storage_);
}

bool JsonValue::is_number() const noexcept {
    return std::holds_alternative<double>(storage_) ||
           std::holds_alternative<std::int64_t>(storage_) ||
           std::holds_alternative<std::uint64_t>(storage_);
}

bool JsonValue::is_string() const noexcept {
    return std::holds_alternative<std::string>(storage_);
}

bool JsonValue::is_array() const noexcept {
    return std::holds_alternative<ArrayType>(storage_);
}

bool JsonValue::is_object() const noexcept {
    return std::holds_alternative<ObjectType>(storage_);
}

bool JsonValue::as_bool() const {
    if (const auto* val = std::get_if<bool>(&storage_)) {
        return *val;
    }
    throw std::runtime_error("JsonValue is not a boolean");
}

std::int64_t JsonValue::as_int64() const {
    if (const auto* val = std::get_if<std::int64_t>(&storage_)) {
        return *val;
    }
    if (const auto* val = std::get_if<std::uint64_t>(&storage_)) {
        return static_cast<std::int64_t>(*val);
    }
    throw std::runtime_error("JsonValue is not an integer");
}

std::uint64_t JsonValue::as_uint64() const {
    if (const auto* val = std::get_if<std::uint64_t>(&storage_)) {
        return *val;
    }
    if (const auto* val = std::get_if<std::int64_t>(&storage_)) {
        return static_cast<std::uint64_t>(*val);
    }
    throw std::runtime_error("JsonValue is not an unsigned integer");
}

double JsonValue::as_double() const {
    if (const auto* val = std::get_if<double>(&storage_)) {
        return *val;
    }
    if (const auto* val = std::get_if<std::int64_t>(&storage_)) {
        return static_cast<double>(*val);
    }
    if (const auto* val = std::get_if<std::uint64_t>(&storage_)) {
        return static_cast<double>(*val);
    }
    throw std::runtime_error("JsonValue is not a number");
}

const std::string& JsonValue::as_string() const {
    if (const auto* val = std::get_if<std::string>(&storage_)) {
        return *val;
    }
    throw std::runtime_error("JsonValue is not a string");
}

const JsonValue::ArrayType& JsonValue::as_array() const {
    if (const auto* val = std::get_if<ArrayType>(&storage_)) {
        return *val;
    }
    throw std::runtime_error("JsonValue is not an array");
}

const JsonValue::ObjectType& JsonValue::as_object() const {
    if (const auto* val = std::get_if<ObjectType>(&storage_)) {
        return *val;
    }
    throw std::runtime_error("JsonValue is not an object");
}

void JsonValue::push_back(JsonValue val) {
    if (!std::holds_alternative<ArrayType>(storage_)) {
        storage_ = ArrayType{};
    }
    std::get<ArrayType>(storage_).push_back(std::move(val));
}

void JsonValue::set(std::string_view key, JsonValue val) {
    if (!std::holds_alternative<ObjectType>(storage_)) {
        storage_ = ObjectType{};
    }
    auto& obj = std::get<ObjectType>(storage_);
    for (auto& item : obj) {
        if (item.first == key) {
            item.second = std::move(val);
            return;
        }
    }
    obj.emplace_back(std::string(key), std::move(val));
}

const JsonValue* JsonValue::find(std::string_view key) const {
    if (const auto* obj = std::get_if<ObjectType>(&storage_)) {
        for (const auto& item : *obj) {
            if (item.first == key) {
                return &item.second;
            }
        }
    }
    return nullptr;
}

std::string JsonValue::serialize(bool pretty, int indent_width) const {
    std::string out;
    out.reserve(256);
    serialize_internal(out, pretty, indent_width, 0);
    return out;
}

void JsonValue::serialize_internal(
    std::string& out,
    bool pretty,
    int indent_width,
    int current_indent) const {

    switch (storage_.index()) {
        case 0: // Null
            out += "null";
            break;
        case 1: // Boolean
            out += std::get<bool>(storage_) ? "true" : "false";
            break;
        case 2: // Integer
            out += std::to_string(std::get<std::int64_t>(storage_));
            break;
        case 3: // UnsignedInteger
            out += std::to_string(std::get<std::uint64_t>(storage_));
            break;
        case 4: { // Number
            double d = std::get<double>(storage_);
            std::ostringstream ss;
            ss.precision(6);
            ss << d;
            out += ss.str();
            break;
        }
        case 5: // String
            out += '"';
            out += escape_json_string(std::get<std::string>(storage_));
            out += '"';
            break;
        case 6: { // Array
            const auto& arr = std::get<ArrayType>(storage_);
            if (arr.empty()) {
                out += "[]";
                break;
            }

            out += '[';
            if (pretty) {
                out += '\n';
            }

            for (std::size_t i = 0; i < arr.size(); ++i) {
                if (pretty) {
                    out.append(current_indent + indent_width, ' ');
                }
                arr[i].serialize_internal(out, pretty, indent_width, current_indent + indent_width);
                if (i + 1 < arr.size()) {
                    out += ',';
                }
                if (pretty) {
                    out += '\n';
                } else if (i + 1 < arr.size()) {
                    out += ' ';
                }
            }

            if (pretty) {
                out.append(current_indent, ' ');
            }
            out += ']';
            break;
        }
        case 7: { // Object
            const auto& obj = std::get<ObjectType>(storage_);
            if (obj.empty()) {
                out += "{}";
                break;
            }

            out += '{';
            if (pretty) {
                out += '\n';
            }

            for (std::size_t i = 0; i < obj.size(); ++i) {
                if (pretty) {
                    out.append(current_indent + indent_width, ' ');
                }
                out += '"';
                out += escape_json_string(obj[i].first);
                out += "\": ";
                obj[i].second.serialize_internal(out, pretty, indent_width, current_indent + indent_width);
                if (i + 1 < obj.size()) {
                    out += ',';
                }
                if (pretty) {
                    out += '\n';
                } else if (i + 1 < obj.size()) {
                    out += ' ';
                }
            }

            if (pretty) {
                out.append(current_indent, ' ');
            }
            out += '}';
            break;
        }
    }
}

} // namespace oscope::reporting
