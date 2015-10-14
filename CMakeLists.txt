cmake_minimum_required(VERSION 3.0)

project(rhapsody2plantuml)

add_subdirectory(sbs2xml)

install(FILES "convert.sh" DESTINATION "." PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
                                                       GROUP_EXECUTE GROUP_READ
                                                       WORLD_EXECUTE WORLD_READ)
install(FILES "README.md" DESTINATION ".")

install(DIRECTORY "xml2plant/" DESTINATION "xml2plant"
        FILES_MATCHING PATTERN "*.py"
        PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
                    GROUP_EXECUTE GROUP_READ
                    WORLD_EXECUTE WORLD_READ)

