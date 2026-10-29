#ifndef OSCOPE_REPORTING_JSON_VALUE_HPP
#define OSCOPE_REPORTING_JSON_VALUE_HPP

#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <utility>
#include <variant>
#include <vector>

namespace oscope::reporting {

enum class JsonType {
    Null,
    Boolean,
    Integer,
    UnsignedInteger,
    Number,
    String,
    Array,
    Object
};

/**
 * @brief Escapes a string to conform with the JSON specification (RFC 8259).
 * Correctly escapes quotation marks, backslashes, control characters (0x00-0x1F),
 * tabs, newlines, carriage returns, form feeds, and backspaces.
 */
std::string escape_json_string(std::string_view input);

/**
 * @brief Lightweight, dependency-free JSON value representation and serializer.
 * Supports null, booleans, signed/unsigned integers, floating-point numbers,
 * strings, arrays, and key-ordered objects.
 */
class JsonValue {
public:
    using ArrayType = std::vector<JsonValue>;
    using ObjectType = std::vector<std::pair<std::string, JsonValue>>;

    JsonValue();
    JsonValue(std::nullptr_t);
    JsonValue(bool val);
    JsonValue(int val);
    JsonValue(long val);
    JsonValue(long long val);
    JsonValue(unsigned int val);
    JsonValue(unsigned long val);
    JsonValue(unsigned long long val);
    JsonValue(double val);
    JsonValue(const char* val);
    JsonValue(std::string val);
    JsonValue(std::string_view val);
    JsonValue(ArrayType arr);
    JsonValue(ObjectType obj);
    JsonValue(std::initializer_list<std::pair<std::string, JsonValue>> init_list);

    static JsonValue null();
    static JsonValue boolean(bool val);
    static JsonValue integer(std::int64_t val);
    static JsonValue unsigned_integer(std::uint64_t val);
    static JsonValue number(double val);
    static JsonValue string(std::string_view val);
    static JsonValue array(ArrayType elements = {});
    static JsonValue object(ObjectType properties = {});

    JsonType type() const noexcept;
    bool is_null() const noexcept;
    bool is_bool() const noexcept;
    bool is_integer() const noexcept;
    bool is_unsigned_integer() const noexcept;
    bool is_number() const noexcept;
    bool is_string() const noexcept;
    bool is_array() const noexcept;
    bool is_object() const noexcept;

    bool as_bool() const;
    std::int64_t as_int64() const;
    std::uint64_t as_uint64() const;
    double as_double() const;
    const std::string& as_string() const;
    const ArrayType& as_array() const;
    const ObjectType& as_object() const;

    // Array manipulation
    void push_back(JsonValue val);

    // Object manipulation (preserves insertion order; updates existing keys)
    void set(std::string_view key, JsonValue val);
    const JsonValue* find(std::string_view key) const;

    /**
     * @brief Serializes the JSON value to a valid JSON string.
     * @param pretty When true, produces formatted, indented output. When false, produces compact JSON.
     * @param indent_width Number of spaces per indentation level.
     * @return Serialized JSON string.
     */
    std::string serialize(bool pretty = true, int indent_width = 2) const;

private:
    using Storage = std::variant<
        std::monostate, // Null
        bool,
        std::int64_t,
        std::uint64_t,
        double,
        std::string,
        ArrayType,
        ObjectType
    >;

    Storage storage_;

    void serialize_internal(std::string& out, bool pretty, int indent_width, int current_indent) const;
};

} // namespace oscope::reporting

#endif // OSCOPE_REPORTING_JSON_VALUE_HPP
