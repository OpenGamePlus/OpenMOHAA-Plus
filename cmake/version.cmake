execute_process(
	COMMAND git rev-parse --is-inside-work-tree
	WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
	OUTPUT_VARIABLE GIT_IS_INSIDE_WORK
	OUTPUT_STRIP_TRAILING_WHITESPACE
)

if ("${GIT_IS_INSIDE_WORK}" STREQUAL "true")
	message(VERBOSE "Git was successfully detected in the source directory. Relevant Git information will be included in the game version.")

	# Current branch
	execute_process(
		COMMAND git branch --show-current
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		OUTPUT_VARIABLE GIT_BRANCH_NAME
		OUTPUT_STRIP_TRAILING_WHITESPACE
	)

	# Revision
	execute_process(
		COMMAND git show -s --format=%H HEAD
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		OUTPUT_VARIABLE GIT_REVISION_HASH
		OUTPUT_STRIP_TRAILING_WHITESPACE
	)

	# Revision
	execute_process(
		COMMAND git show -s --format=%h HEAD
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		OUTPUT_VARIABLE GIT_REVISION_HASH_ABBREVIATED
		OUTPUT_STRIP_TRAILING_WHITESPACE
	)

	# Commit date
	execute_process(
		COMMAND git show -s --format=%ct
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		OUTPUT_VARIABLE GIT_REVISION_DATE
		OUTPUT_STRIP_TRAILING_WHITESPACE
	)

	# Added in OpenMOHAA Plus: configure again when HEAD moves (checkout, commit), so the hash in
	# the version (and the menus' build label) follows the tree instead of the last configure
	execute_process(
		COMMAND git rev-parse --git-path HEAD --symbolic-full-name HEAD --git-path packed-refs
		WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		OUTPUT_VARIABLE GIT_HEAD_PATHS
		OUTPUT_STRIP_TRAILING_WHITESPACE
	)
	string(REPLACE "\n" ";" GIT_HEAD_PATHS "${GIT_HEAD_PATHS}")
	list(LENGTH GIT_HEAD_PATHS GIT_HEAD_PATHS_COUNT)
	if (GIT_HEAD_PATHS_COUNT EQUAL 3)
		list(GET GIT_HEAD_PATHS 0 GIT_HEAD_FILE)
		list(GET GIT_HEAD_PATHS 1 GIT_HEAD_REF)
		list(GET GIT_HEAD_PATHS 2 GIT_PACKED_REFS)
		set(GIT_HEAD_DEPENDS ${GIT_HEAD_FILE} ${GIT_PACKED_REFS})
		if (GIT_HEAD_REF MATCHES "^refs/")
			execute_process(
				COMMAND git rev-parse --git-path ${GIT_HEAD_REF}
				WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
				OUTPUT_VARIABLE GIT_REF_FILE
				OUTPUT_STRIP_TRAILING_WHITESPACE
			)
			list(APPEND GIT_HEAD_DEPENDS ${GIT_REF_FILE})
		endif()
		foreach(GIT_DEPEND ${GIT_HEAD_DEPENDS})
			get_filename_component(GIT_DEPEND "${GIT_DEPEND}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
			if (EXISTS "${GIT_DEPEND}")
				set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GIT_DEPEND}")
			endif()
		endforeach()
	endif()
else()
	message(WARNING "The repository was not detected as a Git working directory. Git information will not be available in the game version number.")
endif()

string(TIMESTAMP GIT_REVISION_DATE_TIME UTC)

set(GIT_REVISION_DATE ${GIT_REVISION_DATE_TIME})
string(TIMESTAMP GIT_REVISION_DATE "%b %d %Y UTC" UTC)

if(NOT GIT_REVISION_BUILD_NUMBER)
	set(GIT_REVISION_BUILD_NUMBER 0)
endif()

if(NOT PRODUCT_VERSION_STAGE)
	set(PRODUCT_VERSION_STAGE "unstable")
endif()

message(VERBOSE "Git branch: ${GIT_BRANCH_NAME}")
message(VERBOSE "Git revision hash: ${GIT_REVISION_HASH}")
message(VERBOSE "Git revision date: ${GIT_REVISION_DATE}")
message(VERBOSE "Git revision build: ${GIT_REVISION_BUILD_NUMBER}")
message(VERBOSE "Stage: ${PRODUCT_VERSION_STAGE}")

configure_file("cmake/q_version.generated.h.in" "${CMAKE_CURRENT_BINARY_DIR}/generated/q_version.generated.h")

list(APPEND CLIENT_INCLUDE_DIRS "${CMAKE_CURRENT_BINARY_DIR}/generated")
list(APPEND SERVER_INCLUDE_DIRS "${CMAKE_CURRENT_BINARY_DIR}/generated")
list(APPEND RENDERER_INCLUDE_DIRS "${CMAKE_CURRENT_BINARY_DIR}/generated")
