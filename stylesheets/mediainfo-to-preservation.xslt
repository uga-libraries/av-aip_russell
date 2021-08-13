<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
	xmlns:premis="http://www.loc.gov/premis/v3"
	xmlns:dc="http://purl.org/dc/terms/"
	xpath-default-namespace="https://mediaarea.net/mediainfo">
	<xsl:output method="xml" indent="yes"/>
	
	<!-- This stylesheet creates preservation.xml from MediaInfo XML output.-->
	<!-- The preservation.xml file is mostly PREMIS, with 2 Dublin Core fields.-->
    <!-- It is used for importing metadata into the ARCHive (digital preservation storage).--> 
    <!--See the UGA Libraries AIP Definition for details.-->

	
	<!-- *************************************************************************************************************** -->
	<!-- **************************************** OVERALL STRUCTURE OF MASTER.XML ************************************** -->
	<!-- *************************************************************************************************************** -->
	
	<xsl:template match="/">
		<preservation>
			<dc:title><xsl:value-of select="$title"/></dc:title>
			<dc:rights>http://rightsstatements.org/vocab/InC/1.0/</dc:rights>
			<aip>
				<premis:object>
					<xsl:call-template name="aip-id"/>
					<xsl:call-template name="aip-version"/>
					<xsl:call-template name="object-category"/>
					<premis:objectCharacteristics>
						<xsl:call-template name="aip-size"/>
						<xsl:call-template name="aip-unique-formats"/>
					</premis:objectCharacteristics>
					<xsl:call-template name="relationship-collection"/>
				</premis:object>
			</aip>
            <!-- Only include the filelist section if there is more than one file in the aip.-->
			<xsl:if test="$file-count > 1">
				<filelist><xsl:apply-templates select="//track[@type='General']"/></filelist>
			</xsl:if>
		</preservation>
	</xsl:template>
	
	
	<!-- *************************************************************************************************************** -->
	<!-- ************************************************* GLOBAL VARIABLES ******************************************** -->
	<!-- *************************************************************************************************************** -->

    <!-- The parameters are given as arguments when running the xslt via the command line or script.-->
    <xsl:param name="department" required="yes"/>
	<xsl:param name="type" required="yes"/>
	<xsl:param name="title" required="yes"/>
	
    <!-- The unique identifier for the group in the ARCHive (digital preservation system).-->
	<xsl:variable name="uri">INSERT-ARCHive-URI/<xsl:value-of select="$department" /></xsl:variable>

    <!-- Combines the identifier from the filename and the aip type.-->
    <xsl:variable name="aip-id">
		<!-- Hargrett oral history identifier format: har-, ua, 2 numbers followed by a dash, 3 numbers followed by an underscore, 4 numbers.-->
		<xsl:if test="$department='hargrett'">
			<xsl:analyze-string select="/MediaInfo/media[1]/@ref" regex="^(har-ua[0-9]{{2}}-[0-9]{{3}}_[0-9]{{4}})">
			 	<xsl:matching-substring>
		 		    <xsl:value-of select="regex-group(1)"/>_<xsl:value-of select="$type"/>
		 		</xsl:matching-substring>
			</xsl:analyze-string>
		</xsl:if>
		<!-- Russell identifier format: rbrl, 3 numbers, 2-5 lowercase letters, a dash, and any number of lowercase letters, numbers or dashes.-->
		<xsl:if test="$department='russell'">
			<xsl:analyze-string select="/MediaInfo/media[1]/@ref" regex="(rbrl\d{{3}}[a-z]{{2,5}}-[a-z0-9-]+)">
			 	<xsl:matching-substring>
		 		    <xsl:value-of select="regex-group(1)"/>_<xsl:value-of select="$type"/>
		 		</xsl:matching-substring>
			</xsl:analyze-string>
		</xsl:if>
	</xsl:variable>

    <!-- The start of the identifier in the filename.-->
    <!-- The pattern match starts from the beginning because the collection id is repeated in the filepath.-->
    <xsl:variable name="collection-id">
		<!-- Hargrett oral history identifier format: har-, ua, 2 numbers followed by a dash, 3 numbers followed by an underscore, 4 numbers.-->
		<xsl:if test="$department='hargrett'">
			<xsl:analyze-string select="/MediaInfo/media[1]/@ref" regex="^(har-ua[0-9]{{2}}-[0-9]{{3}})">
				<xsl:matching-substring>
                	<xsl:value-of select="regex-group(1)"/>
            	</xsl:matching-substring>
			</xsl:analyze-string>
		</xsl:if>
		<!-- Russell identifier format: rbrl followed by 3 numbers.-->
		<xsl:if test="$department='russell'">
			<xsl:analyze-string select="/MediaInfo/media[1]/@ref" regex="^(rbrl\d{{3}})">
				<xsl:matching-substring>
                	<xsl:value-of select="regex-group(1)"/>
            	</xsl:matching-substring>
			</xsl:analyze-string>
		</xsl:if>
	</xsl:variable>
		
	<!-- File count to use in testing when aips are treated differently if they have one or multiple files.-->
	<xsl:variable name="file-count">
		<xsl:value-of select="count(/MediaInfo/media)"/>
	</xsl:variable>

	
	<!-- *************************************************************************************************************** -->
	<!-- *********************************************** FORMAT TEMPLATES ********************************************** -->
	<!-- *************************************************************************************************************** -->

    <!-- These templates are used for making components of the format elements in both the aip and filelist sections. -->

    <!-- Structures the format information when the MediaInfo includes the Format field in the general track.-->
    <!-- Includes the format name, the version if one is present, and a note with what version of MediaInfo was used.-->
    <xsl:template match="Format">
        <premis:format>
            <premis:formatDesignation>
                <premis:formatName>
                    <xsl:value-of select="."/>
                </premis:formatName>
                <!-- Version may come any of the tracks, depending on the format.-->
                <xsl:apply-templates select="../../track/Format_Version"/>
            </premis:formatDesignation>
            <xsl:call-template name="mediainfo-format-note"/>
        </premis:format>
    </xsl:template>

    <!-- Structures the format information when the MediaInfo has the FileExtension but not Format format field in the general track.-->
    <!-- Includes the format extension as the name, the version if one is present, and a note with what version of MediaInfo was used.-->
    <!-- The test for if Format is not present is done when the template is applied.-->
    <xsl:template match="FileExtension">
        <premis:format>
            <premis:formatDesignation>
                <premis:formatName>
                    <xsl:value-of select="."/>
                </premis:formatName>
                <!-- Version may come any of the tracks, depending on the format.-->
                <xsl:apply-templates select="../../track/Format_Version"/>
            </premis:formatDesignation>
            <xsl:call-template name="mediainfo-extension-note"/>
        </premis:format>
    </xsl:template>

    <!-- Creates the version element if the value of the version is not 0.-->
    <!-- A version of 0 is present for some formats and is not a meaningful version number.-->
	<xsl:template match="Format_Version">
		<xsl:if test="not(.='0')">
			<premis:version>
				<xsl:value-of select="."/>
			</premis:version>
		</xsl:if>
	</xsl:template>

    <!-- Note with the MediaInfo version for when the format name comes from the Format field.-->
	<xsl:template name="mediainfo-format-note">
		<premis:formatNote>
			<xsl:text>Format identified by MediaInfo version </xsl:text>
			<xsl:value-of select="/MediaInfo/@version"/>
			<xsl:text>.</xsl:text>
		</premis:formatNote>
	</xsl:template>

    <!-- Note with the MediaInfo version for when the format names comes from the FileExtension field.-->
	<xsl:template name="mediainfo-extension-note">
        <premis:formatNote>
            <xsl:text>Unable to identify format. Instead, file extension identified by MediaInfo version </xsl:text>
            <xsl:value-of select="/MediaInfo/creatingLibrary/@version"/>
            <xsl:text>.</xsl:text>
        </premis:formatNote>
	</xsl:template>


	<!-- *************************************************************************************************************** -->
	<!-- ************************************************* AIP TEMPLATES *********************************************** -->
	<!-- *************************************************************************************************************** -->

    <!-- For aips with more than one file, this section has summary information about the aip as a whole.-->
    <!-- For aips with one file, this section has all the details about that file.-->

	<!-- aip id: PREMIS 1.1 (required): type is group uri and value is aip id. -->
	<xsl:template name="aip-id">
		<premis:objectIdentifier>
			<premis:objectIdentifierType><xsl:value-of select="$uri"/></premis:objectIdentifierType>
			<premis:objectIdentifierValue><xsl:value-of select="$aip-id"/></premis:objectIdentifierValue>
		</premis:objectIdentifier>
	</xsl:template>
	
    <!-- aip version: PREMIS 1.1 (required): type is aip uri and value is default version of 1.-->
	<xsl:template name="aip-version">
		<premis:objectIdentifier>
			<premis:objectIdentifierType>
				<xsl:value-of select="$uri"/>/<xsl:value-of select="$aip-id"/>
			</premis:objectIdentifierType>
			<premis:objectIdentifierValue>1</premis:objectIdentifierValue>
		</premis:objectIdentifier>
	</xsl:template>

    <!-- aip object category: PREMIS 1.2 (required).-->
    <!-- Value is "representation" if there is more than one file or "file" if there is only one file.-->
	<xsl:template name="object-category">
		<premis:objectCategory>
			<xsl:if test="$file-count > 1">representation</xsl:if>
			<xsl:if test="$file-count = 1">file</xsl:if>
		</premis:objectCategory>
	</xsl:template>

    <!-- aip size: PREMIS 1.5.3 (optional): sum of every file size in bytes, formatted as a whole number.-->	
	<xsl:template name="aip-size">
		<premis:size>
			<xsl:value-of select="format-number(sum(/MediaInfo/media/track[@type='General']/FileSize), '#')"/>
		</premis:size>
	</xsl:template>
	
    <!-- aip format list: PREMIS 1.5.4 (required): a unique list of file formats in the aip.-->
    <!-- Format names are from the Format field, or if there is not one then the FileExtension field.-->
    <!-- Uniqueness is determined by the format name and version number.-->
	<xsl:template name="aip-unique-formats">
        <xsl:for-each-group select="//track[@type='General']/Format" group-by="concat(., ../../track/Format_Version[not(.='0')])">
            <xsl:sort select="current-grouping-key()" />
            <xsl:apply-templates select="."/>
        </xsl:for-each-group>

        <xsl:for-each-group select="//track[@type='General']/FileExtension[not(following-sibling::Format)]" group-by="concat(., ../../track/Format_Version)">
        <xsl:sort select="current-grouping-key()" />
            <xsl:apply-templates select="."/>
        </xsl:for-each-group>
	</xsl:template>

	<!-- aip relationship to collection: PREMIS 1.13 (required if applicable).-->
    <!-- Type is the group uri and value is the collection id.-->
	<xsl:template name="relationship-collection">
		<premis:relationship>
			<premis:relationshipType>structural</premis:relationshipType>
			<premis:relationshipSubType>Is Member Of</premis:relationshipSubType>
			<premis:relatedObjectIdentifier>
				<premis:relatedObjectIdentifierType><xsl:value-of select="$uri"/></premis:relatedObjectIdentifierType>
				<premis:relatedObjectIdentifierValue><xsl:value-of select="$collection-id"/></premis:relatedObjectIdentifierValue>
			</premis:relatedObjectIdentifier>
		</premis:relationship>
	</xsl:template>
	
	
	<!-- *************************************************************************************************************** -->
	<!-- *********************************************** FILELIST TEMPLATES ******************************************** -->
	<!-- *************************************************************************************************************** -->
	
    <!-- Detailed information about each file in the aip.-->
    <!-- Only included if there is more than one file in the aip. If there is one file, the aip section has sufficient information.-->

	<!-- Creates the structure for the premis:object for each file in the aip.-->
	<xsl:template match="//track[@type='General']">
		<premis:object>
			<xsl:apply-templates select="CompleteName"/>
			<premis:objectCategory>file</premis:objectCategory>
			<premis:objectCharacteristics>
				<xsl:apply-templates select="FileSize"/>
				<xsl:apply-templates select="Format | FileExtension[not(following-sibling::Format)]" />
			</premis:objectCharacteristics>
			<xsl:call-template name="relationship-aip"/>
		</premis:object>
	</xsl:template>
	
    <!-- file id: PREMIS 1.1 (required): type is aip uri and value is file identifier.-->
    <!-- The file identifier is the filepath starting after the objects folder and the filename.-->
	<xsl:template match="CompleteName">
		<premis:objectIdentifier>
			<premis:objectIdentifierType>
				<xsl:value-of select="$uri"/>/<xsl:value-of select="$aip-id"/>
			</premis:objectIdentifierType>
			<premis:objectIdentifierValue>
				<xsl:analyze-string select="." regex="/objects/(.*)">
					<xsl:matching-substring>
                        <xsl:sequence select="regex-group(1)"/>
                    </xsl:matching-substring>
				</xsl:analyze-string>
			</premis:objectIdentifierValue>
		</premis:objectIdentifier>	
	</xsl:template>
	
    <!-- file size: PREMIS 1.5.3 (optional): the file size in bytes, formatted as a whole number.-->
	<xsl:template match="FileSize">
		<premis:size><xsl:value-of select="format-number(., '#')"/></premis:size>
	</xsl:template>
	
    <!-- file relationship to aip: PREMIS 1.13 (required if applicable).-->
    <!-- Type is group uri and value is aip id.-->
	<xsl:template name="relationship-aip">
		<premis:relationship>
			<premis:relationshipType>structural</premis:relationshipType>
			<premis:relationshipSubType>Is Member Of</premis:relationshipSubType>
			<premis:relatedObjectIdentifier>
				<premis:relatedObjectIdentifierType><xsl:value-of select="$uri"/></premis:relatedObjectIdentifierType>
				<premis:relatedObjectIdentifierValue><xsl:value-of select="$aip-id"/></premis:relatedObjectIdentifierValue>
			</premis:relatedObjectIdentifier>
		</premis:relationship>
	</xsl:template>
	
</xsl:stylesheet>
